

from msaf.models import *
from msaf.lib.querycmd import parse_querycmd
from msaf.lib.queryfuncs import *
from sqlalchemy import extract
from pandas import DataFrame, pivot_table
from io import StringIO


def batchreport( batchcode, markers, infile, outfile, options = [] ):
    """ batchreport

        returns a dict
    """

    d = {}

    batch = Batch.search( batchcode )
    if not batch:
        return RuntimeError('Batch with code: %s is not found' % batchcode)

    sample_ids = dbsession.query(Sample.id).filter( Sample.batch_id == batch.id )

    alleles = get_sample_alleles( sample_ids, 2, 0, 0.75 )

    df = get_sample_dataframe( sample_ids, location_level=3 )

    d['sample_size'] = sample_ids.count()
    d['dataframe'] = df
    d['locations'] = report_by_location( df )
    d['years'] = report_by_year( df )

    df = get_marker_dataframe( sample_ids )
    d['markers'] = report_by_marker( df )
    d['marker_quality'] = report_marker_quality( d['markers'], d['sample_size'] )

    allalleles_df = MarkerDF.get_all_alleles( sample_ids )
    d['markers_summary'] = generate_allele_summary( allalleles_df )
    print(d['markers_summary'])

    format_report( infile, outfile, d )

    return {}


def get_sample_dataframe( sample_ids, location_level=4 ):
    """ return a pandas dataframe of sample_id, location_id and year """

    q = dbsession.query( Sample.id, Sample.location_id, extract('year', Sample.collection_date)
        ).filter( Sample.id.in_( sample_ids ) )

    df = DataFrame([ (sample_id, Location.get(location_id).render(level=location_level), year)
                        for (sample_id, location_id, year) in q ])
    df.columns = ( 'sample_id', 'location', 'year' )

    return df


def report_by_location( df ):
    return pivot_table( df, rows='location', values='sample_id', aggfunc=len)


def report_by_year( df ):
    return pivot_table( df, rows=['year', 'location'], aggfunc=len)


def get_marker_dataframe( sample_ids ):
    """ return a pandas dataframe of marker_id, sample_id, value """

    q = dbsession.query( AlleleSet.sample_id, Allele.marker_id, Allele.value, Allele.height ).join( Allele ).filter( AlleleSet.sample_id.in_( sample_ids ) )

    df = DataFrame( [ (marker_id, sample_id, value, height) for (sample_id, marker_id, value, height) in q ] )
    df.columns = ( 'marker_id', 'sample_id', 'value', 'height' )

    return df


def report_by_marker( df ):
    unique_sample_df = df.drop_duplicates( ['marker_id', 'sample_id'] )
    return pivot_table( unique_sample_df, rows='marker_id', values='sample_id', aggfunc=len)


def report_marker_quality( table, sample_size ):
    """ table is result of report_by_marker
        row := code, id, failed, proportion_failed, included
    """

    result = []

    for marker_id, sample_N in table.iteritems():
        marker = Marker.get( marker_id )
        failed_marker = sample_size - sample_N
        prop_failed_marker = failed_marker / sample_size
        result.append( (marker.code, marker.id, failed_marker, prop_failed_marker,
                True if prop_failed_marker < 0.1 else False ) )

    result.sort()
    return result


def report_marker_summary( df ):
    """ df: data frame with (marker_id, sample_id, value)
    """
    # get unique alleles, mean, median & max allele per sample, and He

    markers = {}

def get_sample_alleles( sample_ids, marker_id, signal_threshold = 0, percentage_threshold = 0 ):

    samples_with_marker = {}
    samples_with_allele = {}

    alleles = {}
    allele_count = 0

    # get AlleleSet with (sample_id, value, size, height)
    q = dbsession.query( AlleleSet.sample_id, Allele.value, Allele.size, Allele.height )

    # join with Allele and only filter for spesific marker_id
    q = q.join(Allele).filter( Allele.marker_id == marker_id )

    # order by sample_id & height
    q = q.order_by( AlleleSet.sample_id, Allele.height.desc() )

    # if we have signal_threshold, use directly
    if signal_threshold > 0:
        q = q.filter( Allele.height > signal_threshold )

    # selecting only sample in sample_ids
    q = q.filter( AlleleSet.sample_id.in_( sample_ids ) )

    highest_signal = 0

    for sample_id, value, size, height in q:

        if sample_id not in samples_with_marker:
            samples_with_marker[ sample_id ] = True
            samples_with_allele[ sample_id ] = 0
            highest_signal = height

        if percentage_threshold > 0:
            # check with highest_signal
            if height / highest_signal < percentage_threshold:
                continue

        samples_with_allele[ sample_id ] += 1
        allele_count += 1

        try:
            alleles[value].append( (size, height) )
        except KeyError:
            alleles[value] = [ (size, height) ]


    results = dict( samples_with_marker = list(samples_with_marker.keys()),
                    samples_with_allele = samples_with_allele,
                    alleles = alleles,
                    allele_count = allele_count
    )
    print(results)
    return results


def format_report( infile, outfile, data ):
    """ from a latex template file, generate pdflatex
    """

    template = open(infile, "rt").read()

    # format TABLE-SAMPLE-LOCATION-BASELINE
    # data['locations']

    buf = []
    buf.append(
        '\\begin{tabular}{lr}\n\\toprule\nLocation & N\\tabularnewline\n\\midrule'
    )
    for (location, n) in data['locations'].iteritems():
        buf.append( "%s & %d \\tabularnewline" % (location, n) )
    buf.append('\\bottomrule\n\\end{tabular}')

    template = template.replace('TABLE-SAMPLE-LOCATION-BASELINE',
            '\n'.join( buf ))

    # format TABLE-SAMPLE-YEAR
    # data['years']

    buf = []
    buf.append(
        '\\begin{tabular}{llr}\n\\toprule\nYear & Location & N\\tabularnewline\n\\midrule'
    )
    Y = data['years']
    current_year = 0
    for (index, n) in Y.itertuples():
        year, location = index
        if year == current_year:
            buf.append( " & %s & %d \\tabularnewline" % (location, n) )
        else:
            current_year = year
            buf.append( "%d & %s & %d \\tabularnewline" % ( year, location, n ) )
    buf.append('\\bottomrule\n\\end{tabular}')

    template = template.replace('TABLE-SAMPLE-YEAR', '\n'.join( buf ))

    # format TABLE-MARKER-QUALITY
    # data['marker_quality']

    buf = []
    buf.append(
        '\\begin{tabular}{lrrc}\n\\toprule\n & \multicolumn{2}{c}{Failed Genotyping} & \\tabularnewline\n\\cmidrule(r){2-3}\nMarker & No. & (\\%) & Included in haplotyping\\tabularnewline\n\\midrule'
    )
    for (code, marker_id, no, prop, state) in data['marker_quality']:
        buf.append('%s & %d & %d \\%% & %s\\tabularnewline' % (
            code, no, prop * 100, 'Yes' if state else 'No' ))
    buf.append('\\bottomrule\n\\end{tabular}')

    template = template.replace('TABLE-MARKER-QUALITY', '\n'.join( buf ))

    open(outfile, 'wt').write( template )


latex_template = '''
'''

        

