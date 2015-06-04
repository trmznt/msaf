
from pandas import DataFrame
from scipy.stats import wilcoxon, kruskal
from msaf.lib.analytics import get_labels
from msaf.models import Marker

import numpy as np

def summarize_he( analytical_sets ):
    """ return he reports with statistical analysis
    """

    reports = {}
    results = []
    #marker_ids = get_marker_ids( analytical_sets )

    all_hes = {}
    for analytical_set in analytical_sets:
        all_hes[analytical_set.get_label()] = analytical_set.get_marker_He()

    he_df = DataFrame( all_hes)

    if len(analytical_sets) == 2:
        # use Mann-Whitney / Wilcoxon test
        reports['test'] = 'Wilcoxon test (paired)'
        labels = get_labels( analytical_sets )
        reports['stats'] = wilcoxon( he_df[labels[0]], he_df[labels[1]] )

    elif len(analytical_sets) > 2:
        # use Kruskal Wallis
        reports['test'] = 'Kruskal-Wallis test'
        labels = get_labels( analytical_sets )
        reports['stats'] = kruskal( * [ he_df[x] for x in labels  ] )

    reports['data'] = he_df
    
    table = df_to_rows( he_df )

    # get StdDev
    table.append( ('',) * (len(he_df.columns) + 1) )
    table.append( ('Mean',) + tuple( np.mean(he_df[x]) for x in he_df.columns) )
    table.append( ('StdDev',) + tuple( np.std(he_df[x]) for x in he_df.columns ) )

    reports['table'] = table

    return reports


def df_to_rows( df ):

    rows = []
    rows.append( ('',) + tuple( df.columns ) )

    for row in df.itertuples():
        rows.append( ( Marker.get(row[0]).code, ) + row[1:] )

    return rows
