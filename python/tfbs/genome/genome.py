# from Bio.SeqRecord import SeqRecord

from tfbs.genome import loader_genomes

class Genome:
    """
    Container class representing a full genome composed of one or more chromids
    (chromosomes or plasmids). Provides convenient constructors for loading
    genome data from files, NCBI accessions, or species queries.
    """
    
    def __init__ (self, chromids, assembly=None, species=None):
        """
        Initialize a Genome object.

        Parameters
        ----------
        chromids : list[SeqRecord]
            List of SeqRecord objects representing chromosomes or plasmids.
        assembly : str, optional
            Assembly identifier or version string.
        species : str, optional
            Species name associated with the genome.
        """
        if not chromids:
            raise ValueError("At least one chromid must be provided")
        self.chromids = chromids
        self.assembly = assembly
        self.species = species
    @classmethod
    def from_file(cls, file_paths):
        """
        Load a genome from one or multiple GenBank files.

        Parameters
        ----------
        file_paths : list[str]
            Paths to GenBank files.

        Returns
        -------
        Genome
            A Genome instance containing all parsed chromids.
        """
        chromids = loader_genomes.load_from_file(file_paths)
        return cls(chromids=chromids)
    
    @classmethod
    def from_accession(cls, accession, email="test@example.com"):
        """
        Load a genome directly from NCBI using one or more accession IDs.
        Parameters:
            accession : str or list[str] --> One or more NCBI accession(s) to fetch.
            email : str --> Email address required by NCBI Entrez.
        Returns:
            A Genome instance containing all retrieved chromids.
        """
        chromids = loader_genomes.load_from_accession(accession, email=email)
        return cls(chromids=chromids)
    @classmethod
    def from_species(cls, species_name):
        """
        Load a genome by species name.
        This method is currently not implemented.
        """
        chromids = loader_genomes.load_from_species(species_name)
        return cls(chromids=chromids, species=species_name)
        
