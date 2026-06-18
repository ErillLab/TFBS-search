import logging
from tfbs.cancel_flag import check_cancel

logger = logging.getLogger(__name__)

def features_to_genes(features):
    """
    Extract gene information from GenBank feature annotations.
    Parameters:
        features : list --> List of SeqFeature objects from a GenBank record.
    Returns:
        list --> List of dictionaries, each representing a gene with locus tag,
            coordinates, strand, protein ID, and product annotation.
    """
    genes = []
    logger.info(f"Extracting genes from features.")
    for feature in features:
        if feature.type == "gene":
            current_gene = {
                "locus_tag": feature.qualifiers.get("locus_tag", ["unknown"])[0],
                "gene_name": feature.qualifiers.get("gene", ["unknown"])[0],
                "start": int(feature.location.start),
                "end": int(feature.location.end),
                "strand": int(feature.location.strand),
                "protein_id": "unknown",
                "product": feature.qualifiers.get("product", ["unknown"])[0]
            }
            genes.append(current_gene)
            logger.debug(
                f"Found gene: {current_gene['locus_tag']} at {current_gene['start']}-{current_gene['end']} (strand {current_gene['strand']}) type: {feature.type}")

        elif feature.type == "CDS":
            protein_id = feature.qualifiers.get("protein_id", ["unknown"])[0]
            product = feature.qualifiers.get("product", ["unknown"])[0]
            
            cds_locus_tags = feature.qualifiers.get("locus_tag", ["unknown"])[0]
            
            for gene in reversed(genes):
                if gene["locus_tag"] == cds_locus_tags:
                    gene["protein_id"] = protein_id
                    if gene["product"] == "unknown":
                        gene["product"] = product
                    break

        
    return genes
    
def distance_to_tls(site_start, site_end,site_strand, gene):
    """
    Compute the distance between a TFBS and the transcription start site (TLS).
    Parameters:
        site_start : int --> Start coordinate of the TFBS.
        site_end : int --> End coordinate of the TFBS.
        site_strand : str --> Strand of the TFBS ('+' or '-').
        gene : dict --> Gene annotation dictionary.
    Returns:
        int --> Signed distance from the TFBS to the gene's TLS.
    """
    if site_strand == "+":
        if gene["strand"] == 1:
            return site_start - gene["start"]
        else:
            return gene["end"] - site_start 
    else:
        if gene["strand"] == 1:
            return site_end - gene["start"]
        else:
            return gene["end"] - site_end 

def classify_region(distance, site_start, site_end, gene, 
                    prev_gene, margin_downstream=50, margin_upstream=250):
    """
    Classify the genomic region of a TFBS relative to a gene.
    Parameters:
        distance : int --> Distance from TFBS to TLS.
        site_start : int --> TFBS start coordinate.
        site_end : int --> TFBS end coordinate.
        gene : dict --> Gene annotation dictionary.
        prev_gene : dict or None --> Previous gene on the same strand.
        margin_downstream : int --> Allowed downstream distance for operator region.
        margin_upstream : int --> Allowed upstream distance for operator region.
    Returns:
        str --> Region classification: "Operator", "Intragenic",
                "Intergenic", or "Unclassified".
    """
    strand = gene["strand"]
    
    if (-margin_upstream) <= distance and distance <= margin_downstream:
        region = "Operator"
    elif gene["start"] <= site_end and site_start < gene["end"]:
        region = "Intragenic"
    elif distance < -margin_upstream:
        if prev_gene is None:
            region = "Intergenic"
        elif strand == 1 and site_start > prev_gene["end"]:
            region = "Intergenic"
        elif strand == -1 and site_end < prev_gene["start"]:
            region = "Intergenic"
        else:
            region = "Unclassified"
    else:
        region = "Unclassified"
    
    return region
    
def find_candidate_genes(site, genes_sequence, 
                         margin_downstream=50, margin_upstream=250):
    """
    Identify the most likely regulated genes for a TFBS.

    Parameters:
        site : dict --> TFBS annotation dictionary.
        genes_sequence : list --> List of gene dictionaries sorted by position.
        margin_downstream, margin_upstream 
    Returns:
        list --> Up to two candidate genes (forward and reverse strand).
    """
    site_start = site["Site Start"]
    site_end = site["Site End"]
    site_strand = site["Site Strand"]
    
    genes_forward = sorted([g for g in genes_sequence if g["strand"] == 1], key=lambda x: x["start"])
    genes_reverse = sorted([g for g in genes_sequence if g["strand"] == -1], key=lambda x: x["end"], reverse=True)
    
    def best_candidate(genes):
    
        candidates = []
        
        for i, gene in enumerate(genes):
            check_cancel()
            prev_gene = genes_sequence[i-1] if i > 0 else None 
            distance = distance_to_tls(site_start, site_end, site_strand, gene)
            region = classify_region(
                distance, site_start, site_end, gene, prev_gene, 
                margin_downstream, margin_upstream)
            
            candidates.append({ 
                "gene": gene,
                "distance": distance,
                "region": region,
            })
            
        operators = [c for c in candidates if c["region"] == "Operator"]
        intragenics = [c for c in candidates if c["region"] == "Intragenic"]
        
        if operators:
            return min(operators, key=lambda x: abs(x["distance"]))
        elif intragenics:
            return min(intragenics, key=lambda x: abs(x["distance"]))
        elif candidates:
            return min(candidates, key=lambda x: abs(x["distance"]))
        return None
    check_cancel()
    best_forward = best_candidate(genes_forward)              
    
    check_cancel()
    best_reverse = best_candidate(genes_reverse)
     
    
    return [c for c in [best_forward, best_reverse] if c is not None]


def compute_operon_intergenic_distance(genes_by_chromid, factor=1.0):
    """
    Compute a dynamic intergenic distance threshold for operon inference based on genome statistics.

    Parameters:
        genome : Genome --> Genome object containing chromids and features.
        factor : float --> Multiplier for the median intergenic distance to set the threshold.
    """
    distances = []
    for chromid_id, genes_seq in genes_by_chromid.items():
        check_cancel()
        for i in range(len(genes_seq)-1):
            check_cancel()
            gene1 = genes_seq[i]
            gene2 = genes_seq[i+1]
            if gene1["strand"] == -1 and gene2["strand"] == 1:
                dist = gene2["start"] - gene1["end"]
                if dist >= 0:
                    distances.append(dist) 
    if not distances: 
        logger.warning("No intergenic distances found for operon inference. Using default threshold of 100.")
        return 100.0
    mean_distance = sum(distances) / len(distances)
    return mean_distance * factor


def infer_operon(gene, genes_sequence, max_distance=100):
    """
    Infer operon membership by scanning adjacent genes on the same strand.

    Parameters:
        gene : dict --> Gene annotation dictionary.
        genes_sequence : list --> List of gene dictionaries sorted by position.
        max_distance : int --> Maximum intergenic distance allowed within an operon.

    Returns:
        list --> List of locus tags belonging to the inferred operon.
    """
    operon = []
    # operon = [{
    #     "locus_tag": gene["locus_tag"],
    #     "distance": 0
    # }]
    current_boundry = gene["end"] if gene["strand"] == 1 else gene["start"]
    index_gene = genes_sequence.index(gene)
    if gene["strand"] == 1:
        for gen in genes_sequence[index_gene+1:]:
            check_cancel()
            if gen["strand"] == 1:
                distance = gen["start"] - current_boundry
                if distance < 0: 
                    distance = 0
                elif distance > max_distance:
                    break

                operon.append({
                    "locus_tag": gen["locus_tag"],
                    "distance": distance
                })

                current_boundry = max(current_boundry, gen["end"])
            else:
                break
    else:
        
        for gen in reversed(genes_sequence[:index_gene]):
            check_cancel()
            if gen["strand"] == -1:           
                distance = current_boundry - gen["end"]
                if distance < 0: 
                    distance = 0
                elif distance > max_distance:
                    break
                operon.append({
                    "locus_tag": gen["locus_tag"],
                    "distance": distance
                })

                current_boundry = min(current_boundry, gen["start"])
          
    return operon

    
def annotate_hit(site, genes_sequence, margin_downstream=50, margin_upstream=250, inter_operons=False, max_distance_operon=100):
    
    """
    Annotate a TFBS with its regulated gene(s) and region classification.

    Parameters:
        site : dict --> TFBS annotation dictionary.
        genes_sequence : list --> List of gene dictionaries sorted by position.
        margin_downstream, margin_upstream
        inter_operons : bool --> Whether to infer operons for each gene.
        max_distance_operon : int --> Maximum distance allowed within operons.

    Returns:
        list --> List of annotation dictionaries for the TFBS.
    """
    
    candidates= find_candidate_genes(
        site, genes_sequence,
        margin_downstream, margin_upstream)
    
    if not candidates:
        return []
    
    operators = [c for c in candidates if c["region"] == "Operator"]
    intragenics = [c for c in candidates if c["region"] == "Intragenic"]
    intergenics = [c for c in candidates if c["region"] == "Intergenic"]
    
    if operators:
        selected = operators + intragenics
    elif intragenics:
        selected = intragenics
    elif intergenics:
        selected = [min(intergenics, key=lambda x: x["distance"])]
    else:
        return []
       
    annotated = []
    for candidate in selected:
        gene = candidate["gene"]
        entry = {
            "Site Mode": candidate["region"],
            "Relative Distance": candidate["distance"],
            "Gene locus tag": gene["locus_tag"],
            "Gene Name": gene["gene_name"],
            "Protein Id": gene["protein_id"],
            "Gene Start": gene["start"],
            "Gene End": gene["end"],
            "Gene Strand": gene["strand"],
            "Gene Product": gene["product"]
        }
        if inter_operons:
            entry["Operon"] = infer_operon(gene, genes_sequence, max_distance=max_distance_operon)
        else:
            # entry["Operon"] = [gene["locus_tag"]]
            entry["Operon"] = ""
        
       
            
        annotated.append(entry)
    return annotated



def find_regulated_genes(genome, sites, margin_downstream=50, margin_upstream=250, infer_operons=False, max_distance_operon=100, double_report=True, genes_by_chromid=None):
    """
    Assign TFBS hits to regulated genes across an entire genome.

    Parameters:
        genome : Genome --> Genome object containing chromids and features.
        sites : list --> List of TFBS dictionaries produced by the scanner.
        margin_downstream, margin_upstream
        infer_operons : bool --> Whether to infer operons for each gene.
        max_distance_operon : int --> Maximum distance allowed within operons.
        double_report : bool --> Whether to report both strand candidates.
    Returns:
        list --> List of fully annotated TFBS entries across the genome.
    """
    sites_by_chromid = {}
    for s in sites:
        sites_by_chromid.setdefault(s["Chromid Id"], []).append(s) 
 
    results = []
    site_counter = 1
    
    for chromid in genome.chromids:        
        check_cancel()
        # genes = features_to_genes(chromid.features)
        # genes_sequence = sorted(genes, key=lambda x: x["start"])
        genes_sequence = genes_by_chromid[chromid.id]
        
        for site in sites_by_chromid.get(chromid.id, []):
            check_cancel()
            annotations = annotate_hit(
                site, genes_sequence, margin_downstream, margin_upstream, infer_operons, max_distance_operon
            )
        
            site_id = site_counter
            site_counter += 1
            
            if not annotations:
                results.append({
                    "Site ID": site_id,
                    "Chromid Id": chromid.id,
                    "Site Score": site["Site Score"],
                    "Site Start": site["Site Start"],
                    "Site End": site["Site End"],
                    "Site Strand": site["Site Strand"],
                    "Site Mode": "Unclassified",
                    "Relative Distance": None,
                    "Gene locus tag": None,
                    "Gene Name": None,
                    "Protein Id": None,
                    "Gene Start": None,
                    "Gene End": None,
                    "Gene Strand": None,
                    "Gene Product": None,
                    "Operon": ""
                })
                continue
                        
            if double_report and len(annotations) > 1:
                annotations_to_report = annotations
            else:
                ops_upstream = [a for a in annotations if a["Site Mode"] == "Operator" and a["Relative Distance"] < 0]
                ops_downstream = [a for a in annotations if a["Site Mode"] == "Operator" and a["Relative Distance"] > 0]
                intra = [a for a in annotations if a["Site Mode"] == "Intragenic"]
                inter = [a for a in annotations if a["Site Mode"] == "Intergenic"]
                if ops_upstream:
                    best_op = min(
                        ops_upstream, key=lambda x: abs(int(x["Relative Distance"]))
                    )
                    annotations_to_report = [best_op]
                elif ops_downstream:
                    best_op = min(
                        ops_downstream, key=lambda x: abs(int(x["Relative Distance"]))
                    )
                    annotations_to_report = [best_op]
                elif intra:
                    annotations_to_report = [intra[0]]
                elif inter:
                    annotations_to_report = [inter[0]]
                else:
                    annotations_to_report = []
                            
            for annotation in annotations_to_report:
                check_cancel()
                results.append({
                    "Site ID": site_id,
                    "Chromid Id": chromid.id,
                    "Site Score": site["Site Score"],
                    "Site Start": site["Site Start"],
                    "Site End": site["Site End"],
                    "Site Strand": site["Site Strand"],
                    
                    **annotation    
                
            })    
    return results
