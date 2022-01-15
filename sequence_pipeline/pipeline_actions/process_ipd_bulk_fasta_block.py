from .s3 import s3Provider

from .common import build_s3_sequence_key, build_s3_constants_key



def process_class_i(raw_class_i_loci, class_i_loci, class_i_starts, species, s3):
    unknown_start = []
    for locus in raw_class_i_loci:
        key = build_s3_sequence_key('raw/' +locus, format='json')
        locus_data, success, errors = s3.get(key)
        for allele_group in locus_data:
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
                                class_i_loci[species][locus] = {'allele_group_count':0,'sequences':{}}
                            if allele_group not in class_i_loci[species][locus]:
                                class_i_loci[species][locus]['sequences'][allele_group] = {'count':0,'alleles':[]}
                                class_i_loci[species][locus]['allele_group_count'] += 1
                            class_i_loci[species][locus]['sequences'][allele_group]['alleles'].append(allele)
                            class_i_loci[species][locus]['sequences'][allele_group]['count'] += 1
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
    key = build_s3_sequence_key('species_map', format='json')
    data, success, errors = s3.get(key)
    key = build_s3_constants_key('class_i_starts')
    class_i_starts, success, errors = s3.get(key)
    class_i_loci = {}
    class_ii_alpha_loci = {}
    class_ii_beta_loci = {}
    for species in data:
        species_data = data[species]
        class_i_loci, unknown_start = process_class_i(species_data['class_i']['alpha'], class_i_loci, class_i_starts, species, s3)
        
        # TODO process Class II
        #for locus in species_data['class_ii']['alpha']:
            #class_ii_alpha_loci.append(locus)
        #for locus in species_data['class_ii']['beta']:
            #class_ii_beta_loci.append(locus)

    return {'class_i_starts':class_i_starts, 'class_i_loci': class_i_loci, 'unknown_start':unknown_start}, success, errors