import math
from Bio.Seq import Seq
import logging
import numpy as np

logger = logging.getLogger(__name__)
    
def integrate_scores(score_forward, score_reverse,integration_log = False ):
    """
    Integrate forward and reverse strand scores into a single site score.
    Parameters:
        score_forward : float or None --> Score on the forward strand.
        score_reverse : float or None --> Score on the reverse strand.
        integration_log : bool --> If True, combine scores using 
            log-sum-exp approximation; otherwise use max().
    Returns:
        float or None --> Integrated score, or None if both scores are missing.
    """
    if score_forward is None and score_reverse is None:
        return None
    elif score_forward is None:
        return score_reverse
    elif score_reverse is None:
        return score_forward
    else:
        if integration_log:
            try:
                return math.log2((2 ** score_forward) + (2 ** score_reverse)) - 1
            except (ValueError, OverflowError):
                return max(score_forward, score_reverse)
        else:
            return max(score_forward, score_reverse)

def scan_sequence(sequence, motif, threshold=0, integration_log=False):
    """
    Scan a DNA sequence for motif occurrences using a PSSM.
    Parameters:
        sequence : str --> DNA sequence to scan.
        motif : Motif --> Motif object containing a PSSM.
        threshold : float --> Minimum PSSM score required to report a hit.
        integration_log : bool --> Whether to integrate strand scores using
            log-based combination.
    Returns:
        list[dict] --> List of detected binding sites with score, coordinates,
            and strand orientation.
    """
    sequence = str(sequence).upper()
    motif_length = motif.length
    pssm = motif.pssm
    forward_hits = {}
    reverse_hits = {}
      
    scores = np.atleast_1d(pssm.calculate(sequence))
    
  
    r_scores = np.atleast_1d(pssm.reverse_complement().calculate(sequence))
    
    pos_forward = np.where(scores >= threshold)[0]
    forward_hits = {pos: scores[pos] for pos in pos_forward}
    pos_reverse = np.where(r_scores >= threshold)[0]
    reverse_hits = {pos: r_scores[pos] for pos in pos_reverse}
   
    results = []
    
    
    for pos in sorted(set(forward_hits) | set(reverse_hits)):
        window = sequence[pos:pos+motif_length]
        score_forward = forward_hits.get(pos)
        score_reverse = reverse_hits.get(pos)
        integrated_score = integrate_scores(score_forward, score_reverse, integration_log=integration_log)
        if integrated_score is None:
            continue
        
        if score_reverse is None:
            strand = '+'
            seq_window = window
        elif score_forward is None:
            strand = '-'
            seq_window = str(Seq(window).reverse_complement())
        elif score_forward >= score_reverse:
            strand = '+' 
            seq_window = window
        else:
            strand = '-'
            seq_window = str(Seq(window).reverse_complement())
            
        
        pos_final = pos + motif_length
        results.append({
            "Site Score": integrated_score,
            "Site Start": pos,
            "Site End": pos_final,
            "Site Strand": strand,
        
        })
    return results

def scan_chromid(chromid, motif, threshold=0, integration_log=False):
    """
    Scan a chromid (chromosome or plasmid) for motif occurrences.
    Parameters:
        chromid : SeqRecord --> Chromid containing an ID and a DNA sequence.
        motif : Motif --> Motif object containing a PSSM.
        threshold : float --> Minimum score required to report a hit.
        integration_log : bool --> Whether to integrate strand scores using
            log-based combination.
    Returns:
        list[dict] --> List of detected binding sites annotated with chromid ID.
    """
    try:
        sequence = str(chromid.seq).upper()
    except Exception as e:
        try:
            sequence = chromid.seq._data.decode("ascii") if isinstance(chromid.seq._data, bytes) else chromid.seq._data
            print("_data ok")
        except Exception as e2:
            print("Error en _data:", e2)
            raise
    
    sequence = sequence.upper()
    
    s_seq = scan_sequence(sequence, motif, threshold, integration_log)
    for result in s_seq:
        result["Chromid Id"] = chromid.id
    return s_seq

def scan_genome(genome, motif, threshold=0, integration_log=False):
    """
    Scan all chromids in a genome for motif occurrences.
    Parameters:
        genome : Genome --> Genome object containing multiple chromids.
        motif : Motif --> Motif object containing a PSSM.
        threshold : float --> Minimum score required to report a hit.
        integration_log : bool --> Whether to integrate strand scores using
            log-based combination.
    Returns:
        list[dict] --> Aggregated list of binding sites across all chromids.
    """
    result = []
    for chromid in genome.chromids:
        chromid_results = scan_chromid(chromid, motif, threshold, integration_log)
        result.extend(chromid_results)
    return result