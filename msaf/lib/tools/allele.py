
from collections import defaultdict
from matplotlib import pyplot as plt
from matplotlib.ticker import MultipleLocator
import numpy as np

from msaf.models import Marker

def summarize_alleles2( analytical_sets, temp_dir = None ):
    """ return a tuple of (report, plot)
    """

    allele_plots = {}
    allele_reports = {}

    for analytical_set in analytical_sets:

        allele_df = analytical_set.get_allele_df()
        report, plot = summarize_alleles3( allele_df )

        allele_reports[ analytical_set.get_label() ] = report
        allele_plots[ analytical_set.get_colour() ] = plot


    # create plots

    if temp_dir:
        plot_file = make_allele_plot2( allele_plots, temp_dir + 'allele_plot.pdf',
            analytical_sets )
    else:
        plot_file = None

    return (allele_reports, plot_file)




def summarize_alleles3( allele_df ):
    """ return a tuple of (dict, dict):
        1dict: alleles: [ (allele, freq, count, mean_height, min_size, max_size, delta), ...]
        2dict: marker: ( [ size, ...], [ height, ....] )
    """

    allele_list = defaultdict(list)
    allele_plot = defaultdict(lambda x = None: ([], []))
    grouped = allele_df.groupby( ['marker_id', 'value'] )

    for (marker_id, allele), df in grouped:

        allele_list[marker_id].append(
            (allele, len(df), np.mean( df['height'] ), min(df['size']), max(df['size']),
                list(df['sample_id']), np.mean( df['size'] ))
        )

        code = Marker.get(marker_id).code
        allele_plot[code][0].extend( df['size'] )
        allele_plot[code][1].extend( df['height'] )
            

    # calculate other stuff

    results = {}

    for marker_id in allele_list:
        alleles = allele_list[marker_id]
        total_allele = sum( x[1] for x in alleles )
        allele_params = [
            (allele, count/total_allele, count, mean_height, min_size, max_size,
                max_size - min_size, sample_ids, mean_size )
            for (allele, count, mean_height, min_size, max_size, sample_ids, mean_size )
            in alleles
        ]

        delta_status = check_delta( allele_params)

        results[marker_id] = dict(
            code = Marker.get(marker_id).code,
            unique_allele = len(allele_params),
            total_allele = total_allele,
            alleles = allele_params,
            delta_status = delta_status )

    return (results, allele_plot)


def make_allele_plot2( data_plots, filename, analytical_sets = None ):

    n = len(data_plots) # number of distinct colors
    markers = set()     # number of markers
    for d in data_plots:
        markers.update( list(data_plots[d].keys()) )
    m = len(markers) + 1


    fig = plt.figure( figsize=(21, 4 * m), dpi=600 )

    axes = []

    for idx, marker in enumerate( sorted(markers) ):

        ax = fig.add_subplot( m, 1, idx + 1 )

        for colour in data_plots:
            data = data_plots[colour][marker]

            ax.vlines( data[0], [0], data[1], colors = [ colour ] )


        ax.get_xaxis().set_tick_params( which='both', direction='out' )
        ax.get_yaxis().set_tick_params( which='both', direction='out' )
        minor_locator = MultipleLocator(1)
        major_locator = MultipleLocator(5)
        ax.get_xaxis().set_major_locator( major_locator )
        ax.get_xaxis().set_minor_locator( minor_locator )

        for label in ax.get_xticklabels():
            label.set_size( 'xx-small' )
        for label in ax.get_yticklabels():
            label.set_size( 'xx-small' )

        ax.set_ylabel( marker )
        ax.set_ylim(0)
        #ax.set_xlim(min(data[0]), max(data[0]))
        ax.set_xlim(auto = True)

        axes.append( ax )

    # create the legend plot by creating dummy

    if analytical_sets:
        lx = fig.add_subplot( m, 1, m )
        for analytical_set in analytical_sets:
            lx.vlines( [0,0], [0], [0,0],
                        colors = [ analytical_set.get_colour() ],
                        label = analytical_set.get_label() )
        leg = lx.legend(ncol = n )
        #lx.set_ylabel( 'Legend' )
        lx.set_axis_off()

    fig.tight_layout()

    fig.savefig( filename )
    plt.close()
    return filename


def summarize_alleles_xxx( allele_df, temp_dir = None ):
    """ return a dict containing:
        alleles: [ (allele, freq, count, mean_height, min_size, max_size, delta), ...]
    """

    allele_list = defaultdict(list)
    allele_plot = defaultdict(lambda x = None: ([], []))
    grouped = allele_df.groupby( ['marker_id', 'value'] )

    for (marker_id, allele), df in grouped:

        allele_list[marker_id].append(
            (allele, len(df), np.mean( df['height'] ), min(df['size']), max(df['size']), list(df['sample_id']))
        )

        if temp_dir:
            code = Marker.get(marker_id).code
            allele_plot[code][0].extend( df['size'] )
            allele_plot[code][1].extend( df['height'] )
            

    # calculate other stuff

    results = {}

    for marker_id in allele_list:
        alleles = allele_list[marker_id]
        total_allele = sum( x[1] for x in alleles )
        allele_params = [
            (allele, count/total_allele, count, mean_height, min_size, max_size,
                max_size - min_size, sample_ids )
            for (allele, count, mean_height, min_size, max_size, sample_ids) in alleles ]

        delta_status = check_delta( allele_params)

        results[marker_id] = dict(
            code = Marker.get(marker_id).code,
            unique_allele = len(allele_params),
            total_allele = total_allele,
            alleles = allele_params,
            delta_status = delta_status )

    if temp_dir:
        plot_file = make_allele_plot( allele_plot, temp_dir + 'allele_plot.pdf' )
    else:
        plot_file = None

    return (results, plot_file)


def check_delta( alleles ):

    # check if only single allele
    if len(alleles) <= 1:
        return [ True ]

    threshold = 1

    delta_status = []
    if alleles[1][0] - alleles[0][0] <= threshold:
        delta_status.append( False )
    else:
        delta_status.append( True )
    for i in range(1, len(alleles) - 1):
        if (    alleles[i][0] - alleles[i-1][0] <= threshold or
                alleles[i+1][0] - alleles[i][0] <= threshold ):
            delta_status.append( False )
        else:
            delta_status.append( True )
    if alleles[-2][0] - alleles[-1][0] == 1:
        delta_status.append( False )
    else:
        delta_status.append( True )

    return delta_status


def make_allele_plot( data_plots, filename ):

    n = len(data_plots)

    fig = plt.figure( figsize=(21, 4 * n), dpi=600 )

    axes = []

    for idx, key in enumerate( sorted(data_plots) ):
        
        data = data_plots[key]

        ax = fig.add_subplot( n, 1, idx )
        ax.vlines( data[0], [0], data[1] )

        ax.get_xaxis().set_tick_params( which='both', direction='out' )
        ax.get_yaxis().set_tick_params( which='both', direction='out' )
        minor_locator = MultipleLocator(1)
        major_locator = MultipleLocator(5)
        ax.get_xaxis().set_major_locator( major_locator )
        ax.get_xaxis().set_minor_locator( minor_locator )

        for label in ax.get_xticklabels():
            label.set_size( 'xx-small' )
        for label in ax.get_yticklabels():
            label.set_size( 'xx-small' )

        ax.set_ylabel( key )

        axes.append( ax )

    fig.savefig( filename )
    plt.close()
    return filename
    


