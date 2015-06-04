
from msaf.lib.analytics import get_haplotypes
from pandas import concat, pivot_table, DataFrame
from matplotlib import pyplot as plt

def summarize_haplotypes( analytical_sets ):

    """ return (no_of_unique_haplotype, freqs) """

    # find haplotype type as well as sums
    df_sets = get_haplotypes(analytical_sets, dropna = True)
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
    all_freqs = []
    labels = []
    haps = []
    for (idx, key) in enumerate( haplotype_key.keys(), start = 1 ):
        freq = len(haplotype_key[key])
        all_freqs.append( freq )
        if freq == 1:
            # as singleton, absorb in to idx 0
            hap_freqs[0] += 1
            k = 0
        else:
            hap_freqs[idx] = freq
            k = idx

        for e in haplotype_key[key]:
            haps.append( k )
            labels.append( df_sets[e[0]][0].get_label() )

    # now we create dataframe of set_name, haplotype_id
    
    df = DataFrame( { 'label': labels, 'haplotype': haps } )
    haplotype_df = pivot_table( df, cols = [ 'haplotype' ], rows = ['label'], values = 'haplotype', aggfunc='count' )

    return ( len(haplotype_key), hap_freqs, all_freqs, haplotype_df )


def plot_haplotype( haplotype_df, directory = None, filename = None ):
    if not directory:
        raise RuntimeError

    if not filename:
        raise RuntimeError

    haplotype_file = directory + filename

    fig = plt.figure()
    fig_ax = fig.add_subplot(111)
    ax = haplotype_df.plot(kind='bar', stacked=True, colormap='gist_ncar_r', ax=fig_ax)
    #fig = ax.get_figure()

    handles, labels = ax.get_legend_handles_labels()
    labels = [ 'Singletons' ] + [ 'Hap%02d' % i for i in range(1, len(labels)) ]
    leg = ax.legend( handles, labels, fontsize='x-small', fancybox=True, bbox_to_anchor=(1,1),
                loc = 'upper left')

    ax.set_xlabel('Differentiation')
    for label in ax.get_xticklabels():
        label.set_rotation(90)
        label.set_size( 'x-small' )

    fig.savefig( haplotype_file, bbox_extra_artists = (leg,), bbox_inches = 'tight' )
    plt.close()
    return haplotype_file

