from common.helpers import fetch_constants
from common.providers import s3Provider, awsKeyProvider

from common.helpers import fetch_constants

import datetime


def process_class_i(raw_class_i_loci, class_i_loci, class_i_starts, species, s3):
    unknown_start = []
    for locus in raw_class_i_loci:
        key = awsKeyProvider().sequence_key('class_i_raw', locus)
        locus_data, success, errors = s3.get(key)
        if success:
            for allele_group in locus_data:
                print (allele_group)
                for allele in locus_data[allele_group]['alleles']:
                    this_sequence = allele['sequence']
                    present = False
                    for class_i_start in class_i_starts:
                        if len(this_sequence) > 250:
                            if class_i_start in this_sequence[:50]:
                                truncated_sequence = this_sequence[this_sequence.index(class_i_start):]
                                if len(truncated_sequence) > 275:
                                    truncated_sequence = truncated_sequence[:275]
                                allele['sequence'] = truncated_sequence
                                if species not in class_i_loci:
                                    class_i_loci[species] = {}
                                if locus not in class_i_loci[species]:
                                    class_i_loci[species][locus] = {'sequences':{}}
                                if allele_group not in class_i_loci[species][locus]:
                                    class_i_loci[species][locus]['sequences'][allele_group] = {'alleles':[]}
                                class_i_loci[species][locus]['sequences'][allele_group]['alleles'].append(allele)
                                present = True
                                break
                    if not present:
                        if len(this_sequence) > 250:
                            unknown_start.append(allele['allele'])
    return class_i_loci, unknown_start


# TODO Class II beta chain processing
def process_class_ii_alpha():
    return {}


# TODO Class II beta chain processing
def process_class_ii_beta():
    return {}



def process_ipd_bulk_fasta(aws_config):
    s3 = s3Provider(aws_config)
    key = awsKeyProvider().metadata_key('sequences', 'species_map')
    data, success, errors = s3.get(key)

    species_list = fetch_constants('species')
    mhc_starts = fetch_constants('mhc_starts')
    class_i_starts = mhc_starts['class_i']['alpha']
    class_i_loci = {}
#    class_ii_alpha_loci = {}
#    class_ii_beta_loci = {}
    for species in data:
        species_data = data[species]
        class_i_loci, unknown_start = process_class_i(species_data['class_i']['alpha'], class_i_loci, class_i_starts, species, s3)
        
        for species_mhc in class_i_loci:
            for locus in class_i_loci[species_mhc]:
                this_species = None
                for species in species_list:
                    if species_mhc == species_list[species]['stem']:
                        this_species = species_list[species]

                if this_species is not None:
                    locus_data = {
                        'sequences':class_i_loci[species_mhc][locus]['sequences'],
                        'last_updates':datetime.datetime.now().isoformat(),
                        'species': {
                            'common_name':this_species['common_name'],
                            'scientific_name':this_species['scientific_name'],
                            'stem':this_species['stem'],
                            'slug':species
                        }
                    }
                    key = awsKeyProvider().sequence_key('class_i', locus)
                    print (locus_data)
                    print (species_mhc)
                    print (key)
                    this_data, success, errors = s3.put(key, locus_data)
                
                else:
                    print ('----------')
                    print (species_mhc)
                    print ('----------')

        # TODO process Class II
        #for locus in species_data['class_ii']['alpha']:
            #class_ii_alpha_loci.append(locus)
        #for locus in species_data['class_ii']['beta']:
            #class_ii_beta_loci.append(locus)

    print (data)

    return {'class_i_starts':class_i_starts, 'class_i_loci': class_i_loci, 'unknown_start':unknown_start}, success, errors