from Bio import SeqIO
import io
from wa_entrez import WAEntrezClient
from pathlib import Path
import logging
import time

logger = logging.getLogger(__name__)
GENBANK_FILE_EXTENSIONS = [".gb", ".gbk", ".genbank", ".gbff"]
def load_from_file(file_paths):
    """
    Load genome records from one or more GenBank files.
    Parameters: 
        file_paths : list[str] --> Paths to GenBank files.
    Returns:
        list[SeqRecord] --> Parsed SeqRecord objects from all provided files.
    """
    records = []
    for path in file_paths:
        path = Path(path)
        if not path.is_file():
            raise ValueError(f"File not found: {path}")
        if path.suffix.lower() not in GENBANK_FILE_EXTENSIONS:
            raise ValueError(f"Unsupported file format: {path.suffix}"
                             f"Supported formats: {GENBANK_FILE_EXTENSIONS}")

        logger.info(f"Loading genome from file: {path}")
        file_records = list(SeqIO.parse(str(path), "genbank"))
        if not file_records:
            raise ValueError(f"No records found in the file: {path}")
        records.extend(file_records)
    logger.info(f"Successfully loaded {len(records)} records from {len(file_paths)} files")
    return records
        
    
def load_from_accession(accession, email="test@example.com"):
    """
    Fetch genome records from NCBI using accession identifiers.

    Parameters: 
        accession : str or list[str] --> One or more NCBI nucleotide accessions.
        email : str --> Email address required by NCBI Entrez.
    Returns:
        list[SeqRecord] --> Parsed SeqRecord objects retrieved from NCBI.
    """
    
    if isinstance(accession, str):
        accession = [accession]
    WAEntrez = WAEntrezClient(email=email)
    records = []
    for acc in accession:
        logger.info(f"Fetching record for accession: {acc}")
        record = []
        try:
            handle = WAEntrez.wa_efetch(db="nucleotide", id=acc, rettype="gbwithparts", retmode="text")
            record = list(SeqIO.parse(io.StringIO(handle), "genbank"))
            handle.close() 
            logger.info(f"Retrieved record for accession: {acc}")
            
        except Exception as e:
            logger.error(f"Error fetching record for accession {acc}: {e}")
        records.extend(record)
        time.sleep(0.5)  # To respect NCBI rate limits
    logger.info(f"Successfully loaded {len(records)} records for {len(accession)} accessions")
    return records
    raise NotImplementedError("Loading from accession is not implemented yet")

def load_from_species(species_name):
    """
    Load genome data by species name.
    This functionality is not implemented yet.
    """
    raise NotImplementedError("Loading from species is not implemented yet")