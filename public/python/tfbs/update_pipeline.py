"""
Persistent TFBS pipeline state for Pyodide.

This module keeps objects in memory between executions so that
only the necessary pipeline stages are recomputed.
"""

from tfbs.genome.genome import Genome
from tfbs.motif.motif import Motif
from tfbs.scan.scanner import scan_genome
from tfbs.scan.annotation import find_regulated_genes
from tfbs.motif.threshold import compute_threshold


PIPELINE_STATE = {
    "genome": None,
    "motif": None,
    "hits": None,
    "annotated": None,
    "params": {},
    "genome_source": None,
    "motif_file": None,
}



def _changed(old, new, key):
    return old.get(key) != new.get(key)


def load_genome(genome_files=None, genome_accession=None):
    """
    Load genome only if changed.
    """

    global PIPELINE_STATE

    source = (tuple(genome_files) if genome_files else None,
              tuple(genome_accession) if genome_accession else None)

    if PIPELINE_STATE["genome_source"] == source:
        return

    if genome_files:
        genome = Genome.from_file(genome_files)

    elif genome_accession:
        genome = Genome.from_accession(genome_accession)

    else:
        raise ValueError("Genome source missing")

    PIPELINE_STATE["genome"] = genome
    PIPELINE_STATE["genome_source"] = source


    PIPELINE_STATE["hits"] = None
    PIPELINE_STATE["annotated"] = None




def load_motif_if_needed(motif_file, params):

    global PIPELINE_STATE

    prev = PIPELINE_STATE["params"]

    need_reload = (
        PIPELINE_STATE["motif"] is None
        or PIPELINE_STATE["motif_file"] != motif_file
        or _changed(prev, params, "pseudocount")
        or _changed(prev, params, "background")
    )

    if not need_reload:
        return

    motif = Motif.load_motif(
        motif_file,
        pseudocount=params["pseudocount"],
        background=params["background"],
    )

    PIPELINE_STATE["motif"] = motif
    PIPELINE_STATE["motif_file"] = motif_file

    PIPELINE_STATE["hits"] = None
    PIPELINE_STATE["annotated"] = None



def scan_if_needed(params):

    global PIPELINE_STATE

    prev = PIPELINE_STATE["params"]

    need_scan = (
        PIPELINE_STATE["hits"] is None
        or _changed(prev, params, "threshold_method")
        or _changed(prev, params, "threshold_value")
        or _changed(prev, params, "integration_log")
    )

    if not need_scan:
        return

    motif = PIPELINE_STATE["motif"]
    genome = PIPELINE_STATE["genome"]

    threshold = compute_threshold(
        motif,
        threshold_method=params["threshold_method"],
        threshold_value=params["threshold_value"],
    )

    hits = scan_genome(
        genome,
        motif,
        threshold=threshold,
        integration_log=params["integration_log"],
    )

    PIPELINE_STATE["hits"] = hits
    PIPELINE_STATE["annotated"] = None


def annotate_if_needed(params):

    global PIPELINE_STATE

    prev = PIPELINE_STATE["params"]

    need_annotation = (
        PIPELINE_STATE["annotated"] is None
        or _changed(prev, params, "margin_upstream")
        or _changed(prev, params, "margin_downstream")
        or _changed(prev, params, "infer_operons")
        or _changed(prev, params, "max_distance_operon")
        or _changed(prev, params, "double_report")
    )

    if not need_annotation:
        return

    genome = PIPELINE_STATE["genome"]
    hits = PIPELINE_STATE["hits"]

    annotated = find_regulated_genes(
        genome,
        hits,
        margin_upstream=params["margin_upstream"],
        margin_downstream=params["margin_downstream"],
        infer_operons=params["infer_operons"],
        max_distance_operon=params["max_distance_operon"],
        double_report=params["double_report"],
    )

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

    load_genome(genome_files, genome_accession)
    load_motif_if_needed(motif_file, params)
    scan_if_needed(params)
    annotate_if_needed(params)

    PIPELINE_STATE["params"] = params.copy()

    return PIPELINE_STATE["annotated"]


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
    }