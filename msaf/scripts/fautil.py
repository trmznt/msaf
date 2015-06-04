# fautil
# command-line utility to perform fragment analysis

import sys, os, io, csv
import argparse, transaction
from msaf.lib.fatools import fautils, traceio
from msaf.models import Batch, Sample, Assay, EK, Panel, dbsession, Marker

from msaf.lib.querycmd import parse_querycmd, get_queries
from msaf.lib.tools.summary import get_filtered_analytical_sets2

from pprint import pprint
from copy import copy



def init_argparser():

    parser = argparse.ArgumentParser( '' )

    parser.add_argument('--batch', required=True,
            help = 'batch code')
    parser.add_argument('--sample', required=False, default='',
            help = 'sample code')
    parser.add_argument('--assay', required=False, default='',
            help = 'assay code')
    parser.add_argument('--marker', required=False, default='',
            help = 'marker code(s)')
    parser.add_argument('--panel', required=False, default='',
            help = 'panel code(s)')


    parser.add_argument('--upload', required=False, default=None,
            help = 'assay file description')
    parser.add_argument('--fsadir', required=False, default='.',
            help = 'directory containing assay files')

    parser.add_argument('--scan', required=False, action='store_true', default=False,
            help = 'scan and call all peaks')
    parser.add_argument('--minrelratio', required=False, type=float, default=-1,
            help = 'minimum relative ratio from median peak height')
    parser.add_argument('--maxrelratio', required=False, type=float, default=-1,
            help = 'maximum relative ratio from median peak height')
    parser.add_argument('--minheight', required=False, type=int, default=-1,
            help = 'minimum rfu for peaks')
    parser.add_argument('--height', required=False, type=int, default=-1,
            help = 'rfu to filter peaks')
    parser.add_argument('--separationtime', required=False, type=float, default=-1,
            help = "initial separation time")
    parser.add_argument('--ladderonly', required=False, action='store_true', default=False,
            help = 'only scan and call laddder peaks')
    parser.add_argument('--nonladder', required=False, action='store_true', default=False,
            help = 'only scan non-ladder channels')
    parser.add_argument('--ignoredpeaks', required=False, nargs='+', type=int, default=[],
            help = 'list of peaks to ignore')

    parser.add_argument('--adjustladder', required=False, action='store_true', default=False,
            help = 'readjust the ladder using the pre-assigned peaks')

    parser.add_argument('--call', required=False, action='store_true', default=False,
            help = 'perform allele calling (sizing) and checking')

    parser.add_argument('--bin', required=False, action='store_true', default=False,
            help = 'perform allele binning')

    parser.add_argument('--adjustbins', required=False, action='store_true', default=False,
            help = 'adjust bins mid point size')

    parser.add_argument('--checkalleles', required=False, action='store_true', default=False,
            help = 'check for stutter and overlap peaks')

    parser.add_argument('--setallele', required=False, action='store_true', default=False,
            help = 'set certain allele')
    parser.add_argument('--value', default='')
    parser.add_argument('--fromtype', default='')
    parser.add_argument('--totype', default='')

    parser.add_argument('--reassign', required=False, action='store_true', default=False,
            help = 'reassign markers and dyes')

    parser.add_argument('--excludedmarker', required=False, default='',
            help = 'excluded marker(s)')

    parser.add_argument('--resetassays', required=False, action='store_true', default=False,
            help = 'reset all assays')

    parser.add_argument('--checkassay', required=False, default=False,
            help = 'check assay file')

    parser.add_argument('--reportqc', required=False, action='store_true', default=False,
            help = 'report all QC (RSS, dp score, etc)' )

    parser.add_argument('--query', required=False, default='',
            help = 'query text')
    parser.add_argument('--min_abs_rfu', required=False, type=int, default=0,
            help = 'minimum absolute rfu')
    parser.add_argument('--min_rel_rfu', required=False, type=float, default=0,
            help = 'minimum relative rfu')


    parser.add_argument('--user', '-u',
            help = 'user name')
    parser.add_argument('--commit', required=False, action='store_true', default=False,
            help = 'commit to database')

    return parser


def main(args):

    if args.commit:
        with transaction.manager:
            do_fautil( args )

    else:
        do_fautil( args )


def do_fautil( args ):

    if args.upload is not None:
        do_upload( args )
    elif args.scan:
        do_scan( args )
    elif args.call:
        do_call( args )
    elif args.checkalleles:
        do_checkalleles( args )
    elif args.bin:
        do_bin( args )
    elif args.resetassays:
        do_resetassays( args )
    elif args.reassign:
        do_reassign( args )
    elif args.adjustbins:
        do_adjustbins( args )
    elif args.adjustladder:
        do_adjustladder( args )
    elif args.reportqc:
        do_reportqc( args )
    elif args.checkassay:
        do_checkassay( args )
    elif args.setallele:
        do_setallele( args )


def do_upload( args ):

    print('Parsing and verifying input file: %s' % args.upload)
    assay_list = []

    batch = Batch.search(args.batch)
    if not batch:
        print('ERROR: batch code not found:', args.batch)
        sys.exit(1)

    batch_id = batch.id

    #infile = open(args.upload)
    #next(infile)

    inrows = csv.reader( open(args.upload), 
                        delimiter = ',' if args.upload.endswith(".csv") else '\t' )
    next(inrows)
    line_count = 1
    counter = 0

    for row in inrows:
        print(row)

        line_count += 1
        #line = line.strip()
        #if not line or line.startswith('#'):
        #    continue
        if not row[0] or row[0].startswith('#'):
            continue

        #elements = line.split('\t')
        #if len(elements) < 3:
        #    raise RuntimeError('Line %d: only has %d item' % (line_count, len(elements)))

        if len(row) < 3:
            raise RuntimeError('Line %d: only has %d item' % (line_count, len(row)))

        with open( args.fsadir + '/' + row[1], 'rb') as f:
            trace = f.read()
            test = traceio.read_abif_stream( io.BytesIO(trace) )

        # sanity check for sample
        sample = Sample.search( row[0], batch_id )
        if not sample:
            raise RuntimeError('Line %d: sample %s does not exist!' % (line_count,
                    row[0]))

        # preparing for multiple panel in a single assay!
        # we deal by uploading the same assay twice with different panel

        panel_names = [ x.strip() for x in row[2].split(',') ]
        panels = []
        for panel_name in panel_names:
            # sanity check for panel
            panel = Panel.search(panel_name)
            if not panel:
                raise RuntimeError('Line %d: panel %s does not exist!' % (line_count,
                        panel_name))

            panels.append( panel )

        excluded_markers = []
        if len(row) >= 4:
            
            options = [ x.strip() for x in row[3].split(';') ]
            for option in options:
                if option.startswith('exclude='):

                    excluded_markers = [ x.strip().lower() for x in option[8:].split(',') ]

        if excluded_markers:
            # check sanity if any of the markers is not in the combined panels
            available_markers = []
            for panel in panels:
                panel_markers = panel.data['markers'].keys()
                available_markers.extend( [ x.lower() for x in panel_markers ] )

            for marker_name in excluded_markers:
                if not marker_name: continue
                if marker_name not in available_markers:
                    raise RuntimeError('Line %d: excluded marker name %s not in panel(s)'
                                    % (line_count, marker_name))

        # up till this stage, the excluded_markers has been verified to only contain
        # marker names of the combined panels

        for panel in panels:

            assay = Assay( filename = row[1], size_standard = 'ladder-unset',
                        panel_id = panel.id, status = 'assay-uploaded',
                        assay_provider_id = batch.assay_provider_id,
                        rawdata = trace )
            sample.assays.append( assay )
            dbsession.flush()
            print('-> Processing for panel: %s' % panel.code)

            markers_to_exclude = []
            panel_data = panel.data
            if excluded_markers:
                markers = [ x.lower() for x in panel_data['markers'].keys() ]
                for marker_name in excluded_markers:
                    if marker_name in markers:
                        markers_to_exclude.append( marker_name )

                assay.strings['exclude'] = ','.join(markers_to_exclude)

            assay.create_channels(panel, markers_to_exclude)

            if len(panels) > 1:
                assay.notes = 'Combined panels: ' + ' '.join(panel_names)

        counter += 1

        print('Assay %s for sample %s has been uploaded successfully.'
                % ( assay.filename, sample.code ))

    print('Successfully uploaded %d assays.' % counter )


def get_assay_list( args ):
    """ returns [ (assay, sample_code), ... ]
    """
    batch = Batch.search( args.batch )
    if not batch:
        print('ERROR: batch code not found:', args.batch)
        sys.exit(1)

    samples = []
    if args.sample:
        samples = args.sample.split(',')

    assays = []
    if args.assay:
        assays = args.assay.split(',')

    panels = []
    if args.panel:
        panel_codes = args.panel.split(',')
        panels = [ Panel.search(code) for code in panel_codes ]

    assay_list = []
    for sample in batch.samples:
        if samples and sample.code not in samples: continue
        for assay in sample.assays:
            if assays and assay.filename not in assays: continue
            if panels and assay.panel not in panels: continue
            assay_list.append( (assay, sample.code) )

    return assay_list


def do_adjustladder( args ):

    print('Adjust the ladder using pre-assigned ladder peaks for batch: %s' % args.batch)

    assay_list = get_assay_list( args )

    for (assay, sample_code) in assay_list:
        print('Adjusting assay %s [%s] ...' % (assay.filename, sample_code))

        pass
        # XXX: todo a lot of stuff


def do_scan( args ):

    print('Scan and call peaks in all channels for batch: %s' % args.batch)

    assay_list = get_assay_list( args )

    scanning_parameter = fautils.LadderScanningParameter()
    if args.minrelratio >= 0:
        scanning_parameter.min_relative_ratio = args.minrelratio
    if args.maxrelratio >= 0:
        scanning_parameter.max_relative_ratio = args.maxrelratio
    if args.minheight >= 0:
        scanning_parameter.min_height = args.minheight
    if args.separationtime >= 0:
        scanning_parameter.init_separation_time = args.separationtime
    if args.height > 0:
        scanning_parameter.height = args.height
    if args.ignoredpeaks:
        scanning_parameter.ignoredpeaks = args.ignoredpeaks

    counter = 0
    for (assay, sample_code) in assay_list:
        print('Scanning assay %s for sample %s ...' % (assay.filename, sample_code))
        counter += 1

        if not args.nonladder:
            # scan ladder peaks with default ladder search parameter
            (score, ladder_alleles) = assay.scan_ladder_peaks( parameter=scanning_parameter,
                                            reset=True)

            print('Assay %s [ %s ] scanned with rss: %4.1f dpscore: %3.3f (%d/%d)' %
                ( assay.filename, sample_code, assay.rss, assay.dpscore,
                            counter, len(assay_list) ))

            if score < 0.9:
                print('WARNING: assay %s for sample %s did not pass ladder QC!\n-- QC Report: %s' %
                        ( assay.filename, sample_code, assay.strings['qcreport'] ))
                continue

        if not args.ladderonly:
            # scan peaks with default search parameter
            allelesets = assay.scan_peaks()
            for alleleset in allelesets:
                if alleleset.marker is None:
                    if alleleset.channel.marker is None:
                        raise RuntimeError('alleleset.channel.marker can not be None!')
                    raise RuntimeError('alleleset.marker can not be None!!')
                print('-- Dye %s / %s registered alleles: %d' % (
                            alleleset.channel.dye, alleleset.marker.code,
                            len(alleleset.alleles))
                    )
            print('Assay %s [ %s ] scanned for signal peaks (%d/%d)' %
                ( assay.filename, sample_code, counter, len(assay_list) ))

        sys.stdout.flush()


def do_call( args ):

    print('Calling scanned peaks for batch: %s' % args.batch)

    assay_list = get_assay_list( args )

    counter = 0
    for (assay, sample_code) in assay_list:
        counter += 1
        print('Calling assay %s [ %s ] (%d/%d)...' % 
                (assay.filename, sample_code, counter, len(assay_list)))
        if assay.score < 0.5:
            continue

        allelesets = assay.call_peaks()

        sys.stdout.flush()


def do_bin( args ):

    print('Binning called peaks for batch: %s' % args.batch)

    assay_list = get_assay_list( args )
    if args.marker:
        marker_codes = args.marker.split(',')
        markers = [ Marker.search( code ) for code in marker_codes ]
    else:
        markers = None

    if markers:
        print('Markers: %s' % ( ' '.join( m.code for m in markers )))

    for (assay, sample_code) in assay_list:
        print('Binning assay %s [ %s ]...' % (assay.filename, sample_code))

        assay.bin_peaks(markers)


def do_checkalleles( args ):

    print('Checking for stutter and overlap peaks for batch: %s' % args.batch)

    assay_list = get_assay_list( args )

    parameter = fautils.ScanningParameter()

    counter = 0
    for (assay, sample_code) in assay_list:
        counter += 1

        if assay.score < 0.9:
            print('Assay %s [ %s ] has low score and will not be checked (%d/%d)' %
                (assay.filename, sample_code, counter, len(assay_list)))
        else:
            allelesets = []
            for channel in assay.channels:
                if channel.status == 'channel-ladder':
                    continue
                alleleset = channel.get_latest_alleleset()
                fautils.check_stutter_peaks(
                    list(alleleset.alleles), parameter.stutter_threshold )
                allelesets.append( alleleset )
            fautils.check_overlap_peaks( allelesets, parameter.overlap_threshold )
            print('Assay %s [ %s ] has been checked (%d/%d)' %
                (assay.filename, sample_code, counter, len(assay_list)))


def do_checkartifacs( args ):

    print('Checking for artifacts (adjacent bins) for batch: %s' % args.batch)

    assay_list - get_assay_list( args )

    if args.marker:
        marker_codes = args.marker.split(',')
        markers = [ Marker.search( code ) for code in marker_codes ]
    else:
        markers = None
    
    counter = 0
    for (assay, sample_code) in assay_list:
        counter += 1

        for channel in assay.channels:
            if channel.status == 'channel-ladder':
                continue
            if markers and channel.marker not in markers:
                continue
            alleleset = channel.get_latest_alleleset()
            alleleset = [ a for a in alleleset if a.type == 'peak-bin' ]
            alleleset.sort( key = lambda x: x.value )
            
            # hasn't finished yet



    


def do_resetassays( args ):

    print('Resetting assays for batch: %s' % args.batch)

    assay_list = get_assay_list( args )
    for (assay, sample_code) in assay_list:
        assay.reset()


def do_reassign( args ):

    assay_list = get_assay_list( args )
    for (assay, sample_code) in assay_list:

        print('Reassigning assay %s [%s]...' % (assay.filename, sample_code))
        if args.excludedmarker:
            excluded_markers = args.excludedmarker.lower().split(',')
        else:
            try:
                exclusion_data = assay.strings['exclude']
                excluded_markers = exclusion_data.split(',')
            except KeyError:
                excluded_markers = None

        assay.assign_channels(excluded_markers = excluded_markers)


def do_adjustbins( args ):

    from msaf.views.utils import parse_base_params
    from msaf.lib.advquerycmd import parse_advquerycmd

    sample_ids = parse_querycmd( '%s[batch] ' % args.batch + args.query )
    marker_codes = args.marker.split(',')

    p = parse_base_params(
            dict(
                queryset = '%s[batch] ' % args.batch + args.query,
                allele_absolute_threshold = args.min_abs_rfu,
                allele_relative_threshold = args.min_rel_rfu,
                sample_quality_threshold = 0,
                marker_quality_threshold = 1 ),
            exclude = [ 'marker' ]
        )

    sample_sets = parse_advquerycmd( p.queryset )

    from msaf.lib.tools.allele import summarize_alleles2

    for marker_code in marker_codes:

        if not marker_code: continue

        print('Adjust bins for marker: %s' % marker_code)
        marker = Marker.search(marker_code)

        p.marker_ids = [ marker.id ]

        #sample_sets, sample_report, marker_report = get_filtered_analytical_sets(
        #        sample_ids = sample_ids,
        #        marker_ids = [ marker.id ],
        #        allele_absolute_threshold = args.min_abs_rfu,
        #        allele_relative_threshold = args.min_rel_rfu,
        #        sample_quality_threshold = 0,
        #        marker_quality_threshold = 1,
        #        spatial_differentiation = -1,
        #        temporal_differentiation = 0 )
        diff_analytical_sets, sample_report, marker_report = get_filtered_analytical_sets2(
                sample_sets = sample_sets,
                baseparams = p,
                spatial_differentiation = -1,
                temporal_differentiation = 0 )

        results, _ = summarize_alleles2( diff_analytical_sets, None )

        pprint(results)

        alleles = results['-'][marker.id]['alleles']

        # new bins
        empirical_bins = {}
        for el in alleles:
            empirical_bins[int(el[0])] = float(el[8])

        # updating the bins
        bins = copy(marker.bins)
        for idx in range(len(marker.bins)):
            tag = bins[idx][1]
            if tag in empirical_bins:
                print('updating: %d -> %3.1f' % (tag, empirical_bins[tag]))
                bins[idx] = [ round(empirical_bins[tag], 1), tag ]

        # force db
        marker.bins = bins


def do_checkassay( args ):

    files = {}

    data = csv.DictReader( open(args.checkassay),
                        delimiter = ',' if args.checkassay.endswith(".csv") else '\t' )
    print(data.fieldnames)

    count = 1
    for r in data:
        assay_file = r['ASSAY']
        if assay_file in files:
            print('Assay duplicated: %s for sample %s panel %s' % (assay_file, r['SAMPLE'], r['PANEL']))
        files[assay_file] = True
        try:
            a = open(args.fsadir + '/' + assay_file)
            a.close()
            count += 1
        except:
            print('Error line: %d' % count)
            print('Sample: %s' % r['SAMPLE'])
            raise


def do_reportqc( args ):

    assay_list = get_assay_list( args )
    for (assay, sample_code) in assay_list:
        print( 'Sample: %s assay: %s RSS: %6.3f' % (sample_code, assay.filename, assay.rss) )


def do_setallele( args ):

    if not args.totype:
        print('Allele type has to be set!')
        sys.exit(1)

    marker_codes = args.marker.split(',')
    marker_ids = [ Marker.search(m).id for m in args.marker.split(',') ]
    values = [ int(x) for x in args.value.split(',') ]

    assay_list = get_assay_list( args )

    for (assay, sample_code) in assay_list:
        for c in assay.channels:
            if c.marker_id in marker_ids:
                for allele in c.alleles:
                    if allele.value in values:
                        if args.fromtype and allele.type != args.fromtype: continue
                        allele.type = args.totype
                        print('Sample: %s marker: %s allele %d set to %s' %
                            (sample_code, c.marker.code, allele.value, args.totype))


