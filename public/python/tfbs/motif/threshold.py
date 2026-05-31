def compute_threshold(motif, threshold_value=0.1, threshold_method="direct",  precision=10**4):
    """
    Compute a score threshold for a motif's PSSM.
    Parameters:
        motif : Motif --> A Motif object containing a PSSM and background frequencies.
        threshold_value : float --> Value used by the selected thresholding method.
        threshold_method : str --> Method used to compute the threshold. Supported:
            "direct" (raw score), "fpr", "fnr", "balanced", "patser".
        precision : int --> Precision used when computing score distributions.
    Returns:
        float --> The computed threshold score.
    """
    if threshold_method is None:
        raise ValueError("Threshold method must be specified")
    if (threshold_value is None and threshold_method != "patser"):
        raise ValueError("Threshold value must be specified")
    
    if threshold_method == "direct":
        return threshold_value
    
    distribution = motif.pssm.distribution(
        background=motif.background,
        precision=precision
    )
    if threshold_method == "fpr":
        return distribution.threshold_fpr(threshold_value)
    elif threshold_method == "fnr":
        return distribution.threshold_fnr(threshold_value)
    elif threshold_method == "balanced":
        return distribution.threshold_balanced(threshold_value)
    elif threshold_method == "patser":
        return distribution.threshold_patser()
    else:
        raise ValueError(f"Unknown threshold method: {threshold_method}. Supported methods: fpr, fnr, balanced, patser")