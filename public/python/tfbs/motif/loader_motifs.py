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
            # instances.append(Seq(str(record.seq).upper()))
            instances.append(str(record.seq).upper())
        if not instances:
            
            raise ValueError("No sequences found in the file")
        
        instances = validate_motif(instances)
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
    sequences = validate_motif(sequences)
    try:
        # instances = []
        # for seq in sequences:
        #     instances.append(Seq(str(seq).upper()))
        return motifs.create(sequences)
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
    

def load_motif(source):
    """
    Dispatch function that loads a motif based on file extension.
    Parameters:
        source : str --> Path to a motif file in FASTA, TXT, or JASPAR format.
                 or
                 list --> List of motif sequences
    Returns:
        Bio.motifs.Motif -->The parsed motif object.

    """
    if isinstance(source, list):
        return from_list_of_sequences(source)
    elif isinstance(source, str):
        if source.endswith(".fasta") or source.endswith(".fa"):
            return from_fasta(source)
        elif source.endswith(".txt"):
            return from_text_file(source)
        elif source.endswith(".jaspar"):
            return from_jaspar(source)
        else:
            logger.error(f"Unsupported file format: {source}")
            raise ValueError(f"Unsupported file format: {source}")
        
        
def validate_motif(seq_list):
    """
    Validate that the input file is a proper motif.
    Parameters:
        seq_list : list[str] --> List of sequences to validate as a motif.
    """
    if not seq_list:
        raise ValueError("Motif file is empty.")
    seq_list = [s.strip().upper() for s in seq_list if s.strip()]
    
    for s in seq_list:
        if any(c not in "ACGT" for c in s):
            raise ValueError(f"Motif sequences must contain only A, C, G, T characters, sequence '{s}' is not valid.")
    
    lenght = {len(s) for s in seq_list}
    if len(lenght) != 1:
        raise ValueError(f"All motif sequences must be of the same length")
    
    if len(seq_list) < 2:
        raise ValueError(f"Motif must contain at least 2 sequences to be valid")
    
    return seq_list