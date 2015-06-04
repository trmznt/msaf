
from msaf.lib.queryfuncs import AlleleDF
from pandas import pivot_table

def dominant_genotypes( sample_ids, threshold, marker_ids ):

    allele_df = AlleleDF.get_dominant_alleles( sample_ids, marker_ids )

    if allele_df is None:
        return []

    genotypes = pivot_table( allele_df, rows = 'sample_id', cols = 'marker_id',
                                values = 'value' )
    return genotypes.dropna()


def mcc_genotypes( marker_df ):
    
    raise NotImplemented


def summarize_genotypes( analytical_sets ):
    """ return (no_of_unique_haplotype, freqs) """

    # find haplotype type as well as sums
    df_sets = get_genotypes(analytical_sets, dropna = True)
    genotype_df = concat( [ x[1] for x in df_sets],
                            keys = range(len(df_sets)) )

    haplotype_key = {}

    for e in genotype_df.itertuples():
        key = tuple(e[1:])
        try:
            haplotype_key[key].append( e[0] )
        except KeyError:
            haplotype_key[key] = [ e[0] ]

    hap_freqs = { 0: 0 } 
    for (idx, key) in enumerate( haplotype_key.keys(), start = 1 ):
        freq = len(haplotype_key[key])
        if freq == 1:
            # as singleton, absorb in to idx 0
            hap_freqs[0] += 1
        else:
            hap_freqs[idx] = freq


    return ( len(haplotype_key), hap_freqs )


