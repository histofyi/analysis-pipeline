

class awsKeyProvider():

    def constants_key(self, item:str, privacy:str='public', format:str='json') -> str:
        """
        Function to return the S3 key for a specific constants file

        Args:
            item (str): name of the constants file e.g. 'hetatoms'
            privacy (str): whether the file is public or private (not yet used)
            format (str): defaults to .json. Is used to determine the file extension and how the object is treated on retrieval

        Returns:
            str : the S3 key for the object
        """
        return f'constants/{item.lower()}.{format.lower()}'

    def block_key(self, pdb_code:str, facet:str, domain:str, privacy:str='public') -> str:
        """
        Function to return the S3 key for a specific block of information on a strcuture

        Args:
            pdb_code (str): the pdb code of the structure e.g. '7ejn'
            facet (str): the type of information e.g. 'core'
            domain (str): what type of file it is e.g. 'info'
            privacy (str): whether the file is public or private (not yet used)

        Returns:
            str : the S3 key for the object
        """
        return f'structures/{domain.lower()}/{privacy.lower()}/{facet.lower()}/{pdb_code.lower()}.json'


    def structure_key(self, pdb_code:str, structure_contents:str, privacy:str='public') -> str:
        """
        Function to return the S3 key for a specific structure file

        Args:
            pdb_code (str): the pdb code of the structure e.g. '7ejn'
            structure_contents (str): the part of the structure e.g. 'raw', 'aligned', 'peptide', 'solvent', 'abd'
            privacy (str): whether the file is public or private (not yet used)

        Returns:
            str : the S3 key for the object
        """
        return f'structures/files/{privacy.lower()}/{structure_contents.lower()}/{pdb_code.lower()}.pdb'


    def cif_file_key(self, assembly_identifier, structure_contents:str, privacy:str='public') -> str:
        """
        Function to return the S3 key for a specific cif assembly file

        Args:
            pdb_code (str): the pdb code of the structure e.g. '7ejn'
            structure_contents (str): the part of the structure e.g. 'raw', 'aligned', 'peptide', 'solvent', 'abd'
            privacy (str): whether the file is public or private (not yet used)

        Returns:
            str : the S3 key for the object
        """
        return f'structures/files/{privacy.lower()}/{structure_contents.lower()}/{assembly_identifier}.cif'


    def sequence_key(self, mhc_class:str, locus:str, privacy:str='public') -> str:
        """
        Function to return the S3 key for a specific set of sequences (a locus)

        Args:
            mhc_class (str): the type of MHC molecule e.g. 'class_i'
            locus (str): name of the locus in IPD nomenclature e.g. 'hla-a'
            privacy (str): whether the file is public or private (not yet used)

        Returns:
            str : the S3 key for the object
        """
        return f'sequences/files/{privacy.lower()}/{mhc_class.lower()}/{locus.lower()}.json'


    def set_key(self, set_slug:str, set_type:str, context:str, privacy:str='public') -> str:
        """
        Function to return the S3 key for a specific itemset file

        Args:
            set_slug (str): slug of the itemset e.g. 'class_i_with_peptide'
            set_type (str): whether the set is about structures, or other types of sets (not yet used)
            privacy (str): whether the file is public or private (not yet used)

        Returns:
            str : the S3 key for the object
        """
        return f'sets/{privacy.lower()}/{set_type.lower()}/{context.lower()}/{set_slug.lower()}.json'





