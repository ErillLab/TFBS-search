import logging
from Bio.Seq import Seq
from Bio import SeqIO, motifs


logger = logging.getLogger(__name__)

FASTA_EXTENSIONS = [".fasta", ".fa"]
TEXT_EXTENSIONS = [".txt"]  
JASPAR_EXTENSIONS = [".jaspar"]

def from_fasta(file_path):
    
    """
    Load a motif from a FASTA file containing aligned binding site sequences.
    The function reads all sequences, converts them to uppercase, wraps them
    as Biopython Seq objects, and constructs a motif using motifs.create().

    Parameters:
        file_path : str --> Path to a FASTA file containing motif instances.
    Returns: 
        Bio.motifs.Motif --> A Biopython motif object created from the provided FASTA sequences.
    """  
    try:
        instances = []
        for record in SeqIO.parse(file_path, "fasta"):
            instances.append(Seq(str(record.seq).upper()))
        if not instances:
            raise ValueError("No sequences found in the file")
        
        return motifs.create(instances)
     
    except Exception as e:
        logger.error(f"Error loading motif from FASTA file: {e}")
        raise ValueError(f"Error loading motif from FASTA file: {e}")   
    
def from_list_of_sequences(sequences):
    """
    Create a motif directly from a list of raw sequence strings.
    Parameters
        sequences : list[str] --> List of DNA sequences representing motif instances.
    Returns: 
        Bio.motifs.Motif --> A motif constructed from the provided sequences.
    """
    try:
        instances = []
        for seq in sequences:
            instances.append(Seq(str(seq).upper()))
        return motifs.create(instances)
    except Exception as e:
        logger.error(f"Error creating motif from sequences: {e}")
        raise ValueError(f"Error creating motif from sequences: {e}")
    
def from_text_file(file_path):
    """
    Load motif instances from a plain text file, one sequence per line.
    Parameters:
        file_path : str --> Path to a text file containing motif sequences.
    Returns:
        Bio.motifs.Motif --> A motif constructed from the sequences in the file.
    """
    try:
        with open(file_path) as f:
            sequences = [line.strip().upper() for line in f if line.strip()]
        return from_list_of_sequences(sequences,)
    except Exception as e:
        logger.error(f"Error loading sequences from text file: {e}")
        raise ValueError(f"Error loading sequences from text file: {e}")

def from_jaspar(file_path):
    """
    Load a motif from a JASPAR-formatted file.
    Parameters:
        file_path : str --> Path to a JASPAR motif file.
    Returns: 
        Bio.motifs.Motif --> A motif parsed using Biopython's JASPAR reader.
    """
    try:
        with open(file_path) as handle:
            return motifs.read(handle, "jaspar")
    except Exception as e:
        logger.error(f"Error loading motif from JASPAR file: {e}")
        raise ValueError(f"Error loading motif from JASPAR file: {e}")
    

def load_motif(file_path):
    """
    Dispatch function that loads a motif based on file extension.
    Parameters:
        file_path : str --> Path to a motif file in FASTA, TXT, or JASPAR format.
    Returns:
        Bio.motifs.Motif -->The parsed motif object.

    """
    if file_path.endswith(".fasta") or file_path.endswith(".fa"):
        return from_fasta(file_path)
    elif file_path.endswith(".txt"):
        return from_text_file(file_path)
    elif file_path.endswith(".jaspar"):
        return from_jaspar(file_path)
    else:
        logger.error(f"Unsupported file format: {file_path}")
        raise ValueError(f"Unsupported file format: {file_path}")