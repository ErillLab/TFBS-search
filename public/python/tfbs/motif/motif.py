"""
Defines the Motif class, which wraps a Biopython motif object and exposes
a position-specific scoring matrix (PSSM) for use in TFBS scanning.
"""

import logging
from tfbs.motif import loader_motifs
logger = logging.getLogger(__name__)

class Motif:
    """
    Wrapper class around a Biopython motif object.
    This class standardizes motif handling across the pipeline, ensuring
    consistent pseudocounts, background frequencies, and PSSM generation.
    """
    def __init__(self, bio_motif, pseudocount=0.01, alphabet="ACGT", background=None):
        """
        Initialize a Motif wrapper.
        Parameters:
            bio_motif : Bio.motifs.Motif --> The underlying Biopython motif object.
            pseudocount : float --> Pseudocount applied when computing the PSSM.
            alphabet : str --> Allowed nucleotide alphabet.
            background : dict, optional --> Background nucleotide frequencies. 
                If None, uniform frequencies are assumed.
        """
        
        if bio_motif is None:
            raise ValueError("Bio motif cannot be None")
            
        self.motif = bio_motif
        self.alphabet = alphabet
        self.length = bio_motif.length
        self.pseudocount = pseudocount
        self.background = background if background is not None else {nt: 1/len(alphabet) for nt in alphabet}

        
        self.pssm = motif_to_pssm(bio_motif, background=self.background, pseudocount=self.pseudocount)
        
    @classmethod
    def load_motif(cls, file_path):
        """
        Load a motif from a file and wrap it in a Motif instance.
        Parameters:
        file_path : str --> Path to a motif file.
        Returns:
            A fully initialized Motif object.
        """
        bio_motif = loader_motifs.load_motif(file_path)
        return cls(bio_motif)
    @classmethod
    def from_list_of_sequences(cls, seq):
        bio_motif = loader_motifs.from_list_of_sequences(seq)
        return cls(bio_motif)
        
    
        
def motif_to_pssm(motif, background=None,pseudocount=0.01):
    """
    Convert a Biopython motif into a PSSM.
    Parameters:
        motif : Bio.motifs.Motif --> The Biopython motif to convert.
        background : dict, optional --> Background nucleotide frequencies.
        pseudocount : float --> Pseudocount applied to PWM normalization.
    Returns:
        The computed PSSM.
    """
    if background is not None:
        motif.background = background
        
    motif.pseudocounts = pseudocount
    return motif.pssm