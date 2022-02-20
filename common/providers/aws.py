

class awsKeyProvider():

    def constants_key(self, item, privacy='public', format='json'):
        return 'constants/{item}.{format}'.format(item=item, format=format)


    def block_key(self, pdb_code, facet, domain, privacy='public'):
        return 'structures/{domain}/{privacy}/{pdb_code}/{facet}.json'.format(domain=domain, privacy=privacy, pdb_code=pdb_code, facet=facet)


    def structure_key(self, pdb_code, structure_contents, privacy='public'):
        return 'structures/files/{privacy}/{structure_contents}/{pdb_code}.pdb'.format(privacy=privacy,structure_contents=structure_contents,pdb_code=pdb_code)


    def sequence_key(self, mhc_class, locus, privacy='public'):
        return 'sequences/files/{privacy}/{mhc_class}/{locus}.json'.format(privacy=privacy,mhc_class=mhc_class,locus=locus)


    def set_key(self, set_slug:str, set_type:str) -> str:
        return f'sets/{set_type.lower()}/{set_slug.lower()}'





