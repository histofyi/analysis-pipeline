

def class_i_display_name(allele):
    if allele is not None:
        allele_full = allele['mhc_alpha']
        if 'h2-' in allele['mhc_alpha']:
            display_name = f'{allele_full[0].upper()}{allele_full[1:3]}{allele_full[3].upper()}{allele_full[4:]}'
        elif ':' in allele_full:
            n = 2
            groups = allele_full.split(':')
            display_name = ':'.join(groups[:n])
        else:
            display_name = allele_full

        
        return display_name
    else:
        return 'Unmatched'


def resolution_display(resolution):
    if resolution is not None:
        return f'{str(resolution)[:4]}&#8491;'
    else:
        return 'unknown'