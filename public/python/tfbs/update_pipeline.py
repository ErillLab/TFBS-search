"""
Persistent TFBS pipeline state for Pyodide.

This module keeps objects in memory between executions so that
only the necessary pipeline stages are recomputed.
"""

import js

from tfbs.genome.genome import Genome
from tfbs.motif.motif import Motif
from tfbs.scan.scanner import scan_genome
from tfbs.scan.annotation import find_regulated_genes, compute_operon_intergenic_distance, features_to_genes
from tfbs.motif.threshold import compute_threshold
from pyodide.ffi import to_js
from tfbs.cancel_flag import check_cancel, set_cancel_flag, PipelineCancelledError

PIPELINE_STATE = {
    "genome": None,
    "motif": None,
    "hits": None,
    "annotated": None,
    "params": {},
    "genome_source": None,
    "motif_file": None,
    "computed_operon_distance": None,
    "genes_by_chromid": None,
    "computed_threshold": None,
}

# def progress(msg):
#     """
#     Send progress message to JS.
#     """
#     js.postMessage(
#         to_js({"type": "progress", "msg": str(msg)}, dict_converter=True)
#     )


def progress(msg):
    js.postMessage(to_js({
        "type": "progress",
        "msg": str(msg)
    }))
    
def _changed(old, new, key):
    return old.get(key) != new.get(key)


def load_genome(genome_files=None, genome_accession=None):
    """
    Load genome only if changed.
    """

    global PIPELINE_STATE
    check_cancel()
    progress("Loading genome...")

    source = (tuple(genome_files) if genome_files else None,
              tuple(genome_accession) if genome_accession else None)

    if PIPELINE_STATE["genome_source"] == source:
        progress("Genome already loaded - skipping.")
        return

    if genome_files:
        n = len(genome_files)
        for i, f in enumerate(genome_files, 1):
            name = f.split("/")[-1]
            progress(f"Loading genome file {i}/{n}: {name}")
        genome = Genome.from_file(genome_files)

    elif genome_accession:
        n = len(genome_accession)
        for i, acc in enumerate(genome_accession, 1):
            progress(f"Loading genome {i}/{n}: {acc}")
        genome = Genome.from_accession(genome_accession)

    else:
        raise ValueError("Genome source missing")
    
    check_cancel()
    n_chromids = len(genome.chromids)
    progress(f"Genome loaded - {n_chromids} replicon{'s' if n_chromids != 1 else ''}.")
    
    PIPELINE_STATE["genome"] = genome
    PIPELINE_STATE["genes_by_chromid"] = {
        chromid.id: sorted(
            features_to_genes(chromid.features),
            key=lambda g: g["start"]
        )
        for chromid in genome.chromids
    }
    PIPELINE_STATE["genome_source"] = source


    PIPELINE_STATE["hits"] = None
    PIPELINE_STATE["annotated"] = None




def load_motif_if_needed(motif_file, params):

    global PIPELINE_STATE
    
    check_cancel()
    prev = PIPELINE_STATE["params"]

    need_reload = (
        PIPELINE_STATE["motif"] is None
        or PIPELINE_STATE["motif_file"] != motif_file
        or _changed(prev, params, "pseudocount")
        or _changed(prev, params, "background")
    )

    if not need_reload:
        progress("Motif already loaded - skipping.")
        return
    
    name = motif_file.split("/")[-1]
    progress(f"Loading motif from {name}...")
    check_cancel()


    motif = Motif.load_motif(
        motif_file,
        pseudocount=params["pseudocount"],
        background=params["background"],
    )
    dir(motif)

    check_cancel()
    n = motif.length
    progress(f"Motif loaded — {n} sequences.")
    
    PIPELINE_STATE["motif"] = motif
    PIPELINE_STATE["motif_file"] = motif_file

    PIPELINE_STATE["hits"] = None
    PIPELINE_STATE["annotated"] = None



def scan_if_needed(params):

    global PIPELINE_STATE
    
    check_cancel()
    prev = PIPELINE_STATE["params"]

    need_scan = (
        PIPELINE_STATE["hits"] is None
        or _changed(prev, params, "threshold_method")
        or _changed(prev, params, "threshold_value")
        or _changed(prev, params, "integration_log")
    )

    if not need_scan:
        progress("Scan results already cached — skipping.")
        return

    motif = PIPELINE_STATE["motif"]
    genome = PIPELINE_STATE["genome"]
    
    method = params["threshold_method"]
    value = params["threshold_value"]
    progress(f"Computing threshold — method: {method}, value: {value}...")
    check_cancel()

    threshold = compute_threshold(
        motif,
        threshold_method=method,
        threshold_value=value,
    )
    
    PIPELINE_STATE["computed_threshold"] = threshold
    
    
    check_cancel()
    progress(f"Threshold set to {threshold:.3f}.")

    n = len(genome.chromids)
    progress(f"Scanning {n} replicon{'s' if n != 1 else ''} for binding sites...")

    hits = scan_genome(
        genome,
        motif,
        threshold=threshold,
        integration_log=params["integration_log"],
    )
    check_cancel()
    n_hits = sum(len(v) for v in hits.values()) if isinstance(hits, dict) else len(hits)
    progress(f"Scan complete — {n_hits} hit{'s' if n_hits != 1 else ''} found.")

    PIPELINE_STATE["hits"] = hits
    PIPELINE_STATE["annotated"] = None


def annotate_if_needed(params):

    global PIPELINE_STATE
    
    check_cancel()
    prev = PIPELINE_STATE["params"]

    need_annotation = (
        PIPELINE_STATE["annotated"] is None
        or _changed(prev, params, "margin_upstream")
        or _changed(prev, params, "margin_downstream")
        or _changed(prev, params, "infer_operons")
        or _changed(prev, params, "max_distance_operon")
        or _changed(prev, params, "auto_operon_distance")
        or _changed(prev, params, "operon_distance_factor")
        or _changed(prev, params, "double_report")
    )

    if not need_annotation:
        progress("Annotations already cached — skipping.")

        return

    genome = PIPELINE_STATE["genome"]
    hits = PIPELINE_STATE["hits"]
    
    check_cancel()
    if params.get("auto_operon_distance", False):
        factor = params.get("operon_distance_factor", 1.0)
        progress(f"Estimating operon distance from intergenic gaps (factor ×{factor})...")
        estimated_distance = compute_operon_intergenic_distance(PIPELINE_STATE['genes_by_chromid'], factor=factor)
        PIPELINE_STATE["computed_operon_distance"] = round(estimated_distance)
        progress(f"Operon distance set to {estimated_distance} bp (auto).")
    else:
        estimated_distance = params["max_distance_operon"]
        PIPELINE_STATE["computed_operon_distance"] = None
        if params.get("infer_operons", False):
            progress(f"Operon distance set to {estimated_distance} bp (manual).")
    
    up   = params["margin_upstream"]
    down = params["margin_downstream"]
    infer = params.get("infer_operons", False)
    progress(
        f"Annotating hits — window ±{up}/{down} bp"
        + (f", operon inference ON ({estimated_distance} bp max)" if infer else "") + "..."
    )
    check_cancel()
    annotated = find_regulated_genes(
        genome,
        hits,
        margin_upstream=params["margin_upstream"],
        margin_downstream=params["margin_downstream"],
        infer_operons=params["infer_operons"],
        max_distance_operon=estimated_distance,
        double_report=params["double_report"],
        genes_by_chromid=PIPELINE_STATE["genes_by_chromid"],
    )
    
    check_cancel()
    n_ann = len(annotated) if annotated else 0
    progress(f"Annotation complete — {n_ann} regulated gene{'s' if n_ann != 1 else ''} found.")

    PIPELINE_STATE["annotated"] = annotated

def update_pipeline(
    genome_files=None,
    genome_accession=None,
    motif_file=None,
    params=None,
):
    """
    Incremental TFBS pipeline.

    Only recomputes stages affected by parameter changes.
    """

    if params is None:
        raise ValueError("params required")
    print(params["threshold_value"])
    progress("Starting pipeline...")
    check_cancel()

    load_genome(genome_files, genome_accession); check_cancel()
    load_motif_if_needed(motif_file, params); check_cancel()
    scan_if_needed(params); check_cancel()
    annotate_if_needed(params)

    PIPELINE_STATE["params"] = params.copy()
    progress("Pipeline finished.")
    metadata = {
        "num_hits": len(PIPELINE_STATE["hits"]) if PIPELINE_STATE["hits"] else 0,
        "threshold": PIPELINE_STATE["computed_threshold"],
        "motif_length": PIPELINE_STATE["motif"].length,
        "operon_distance_used": PIPELINE_STATE["computed_operon_distance"],
    }
    # return PIPELINE_STATE["annotated"]
    return {
        "annotated": PIPELINE_STATE["annotated"],
        "computed_operon_distance": PIPELINE_STATE["computed_operon_distance"],
        "metadata": metadata,
    }


def reset_pipeline():
    """
    Fully clear cached state.
    """

    global PIPELINE_STATE

    PIPELINE_STATE = {
        "genome": None,
        "motif": None,
        "hits": None,
        "annotated": None,
        "params": {},
        "genome_source": None,
        "motif_file": None,
        "computed_operon_distance": None,
        "genes_by_chromid": None,
    }
    
# Escherichia coli