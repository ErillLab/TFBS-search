from tfbs.genome.genome import Genome
from tfbs.motif.motif import Motif
from tfbs.scan.scanner import scan_genome
from tfbs.scan.annotation import find_regulated_genes
from tfbs.motif.threshold import compute_threshold

def run_pipeline(genome_files=None, genome_accession=None, motif_file=None, params=None):
    """
    Run the full TFBS pipeline.

    Parameters:
        genome_files : list --> Paths or file-like objects for GenBank files.
        motif_file : str or file-like --> Motif file (FASTA/TXT/JASPAR).
        params : dict --> Configuration parameters.

    Returns:
        dict --> {
            "hits": list of annotated hits,
            "metadata": dict with run information
        }
    """
    # print(genome_files)
    # 1. Load genome
    if genome_files:
        genome = Genome.from_file(genome_files)
    elif genome_accession:
        genome = Genome.from_accession(genome_accession)

    # 2. Load motif
    motif = Motif.load_motif(motif_file)

    # 3. Threshold
    threshold_value = params.get("threshold_value", 0.01)
    threshold_method = params.get("threshold_method") or "direct"
    threshold = compute_threshold(motif, threshold_value=threshold_value, threshold_method=threshold_method)
   
    # 4. Scan
    hits = scan_genome(
        genome,
        motif,
        threshold=threshold,
        integration_log=params.get("integration_log", False)
    )

    # 5. Annotate
    annotated = find_regulated_genes(
        genome,
        hits,
        margin_downstream=params.get("margin_downstream", 50),
        margin_upstream=params.get("margin_upstream", 250),
        infer_operons=params.get("infer_operons", False),
        max_distance_operon=params.get("max_distance_operon", 100),
        double_report=params.get("double_report", True)
    )

    # 6. Metadata
    metadata = {
        "motif_length": motif.length,
        "num_hits": len(hits),
        "threshold": threshold,
        "pseudocount": params.get("pseudocount", 0.5),
        "margin_downstream": params.get("margin_downstream", 50),
        "margin_upstream": params.get("margin_upstream", 250),
        "infer_operons": params.get("infer_operons", False),
        "max_distance_operon": params.get("max_distance_operon", 100),
    }

    return {
        "hits": annotated,
        "metadata": metadata,
    }
