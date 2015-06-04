
import sys, os, io
import argparse
import transaction
from msaf.lib.microsatellite import traceio, traceutils, peakutils3 as peakutils
from msaf.models import Sample, Assay, Batch, EK, Channel, Marker, dbsession


# format for path delimited input file:
# SAMPLE_CODE   PANEL_CODE  ASSAY_PATHNAME  ignore=markers


def init_argparser():

    parser = argparse.ArgumentParser( "" )

    parser.add_argument('--batch', required=True,
                help = 'batch code' )
    parser.add_argument('--user', '-u',
                help = 'user name' )
    parser.add_argument('--method', default='cubicspline',
                help = 'method used for peak calling/size determination' )

    parser.add_argument('infile')

    return parser


def main(args):

    with transaction.manager:
        import_assay( args )

    print('Done!')


def import_assay(args):


    print("Parsing and verifying input file: %s" % args.infile)
    assay_list = []

    batch_id = Batch.search(args.batch).id

    infile = open(args.infile)
    next(infile)    # remove first line
    line_count = 1

    for line in infile:

        line_count += 1
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        splits = line.split('\t')
        if len(splits) < 3:
            raise RuntimeError('Line %d: only has %d values' % (line_count, len(splits)))

        # check if file exists, and open it
        #if not os.path.exists( splits[2] ):
        #    print(os.getcwd())
        #    raise RuntimeError('Line %d: file does not exists: %s' % (line_count, splits[1]))

        with open( splits[1], 'rb' ) as f:
            trace = f.read()
            test = traceio.read_abif_stream( io.BytesIO(trace) )

        # check if sample exists
        sample = Sample.search( splits[0], batch_id )
        if not sample:
            raise RuntimeError('Line %d: sample does not exists: %s' % (line_count, splits[0]))

        # check if panel exists
        panel = EK.search( 'panel-' + splits[2] )
        if not panel:
            raise RuntimeError('Line %d: panel does not exists: %s' % (line_count, splits[2]))

        # common check has been performed for this line
        assay_list.append( (sample, panel, trace, splits[1], splits[3] if len(splits) >= 4 else None) )


    # now for each line, try to import to database
    print('Importing assay to database...')

    counter = 0
    for (sample, panel, trace, filename, other_flag) in assay_list:

        assay = Assay( filename = filename,
                size_standard = 'ladder-unset',
                panel_id = panel.id,
                status = 'assay-uploaded',
                rawdata = trace )
        sample.assays.append( assay )
        dbsession.flush()
        assay.create_channels()
        counter += 1

        print('Sample %s assay %s has been imported.' % ( sample.code, assay.filename ))

        # need to find the ladder
        panel_data = panel.data_from_json()
        ladder_name = panel_data['ladder']
        markers = panel_data['markers']

        print('Setting ladder..')
        ladder = EK.search(ladder_name)
        quality = assay.set_ladder( ladder.id )
        if quality < 1.0:
            print('WARNING: Sample %s assay %s cannot be assayed. Ladder QC failed!' %
                        ( sample.code, assay.filename ))
            continue

        marker_names =[ x.lower() for x in markers.values() ]
        excluded_marker = []
        if other_flag:
            flags = [ x.strip() for x in other_flag.split(';') ]
            for flag in flags:
                if flag.startswith('exclude='):
                    marker_list = [ x.lower() for x in flag[8:].split(',') ]
                    for marker_name in marker_list:
                        if marker_name not in marker_names:
                            raise RuntimeError('marker name: %s in flags does not match any' %
                                    marker_name)
                        excluded_marker.append( marker_name )
        print('excluded:', excluded_marker)

        peaks_list = []  # list of [ (channel, peaks), ...]
        if args.method == 'leastsquare':
            method_func = peakutils.least_square( assay.z )
        elif args.method == 'cubicspline':
            ladder_peaks = []
            ladder_sizes = []
            for allele in assay.get_ladder().get_latest_alleles().alleles:
                ladder_peaks.append( allele.peak )
                ladder_sizes.append( allele.size )
            method_func = peakutils.cubic_spline( ladder_peaks, ladder_sizes )
        else:
            raise RuntimeError('Calling method: leastsquare or cubicpsline')
        for dye in markers:
            marker = markers[dye]
            if marker.lower() in excluded_marker:
                continue

            marker_obj = Marker.search(marker)
            print('Processing dye: %s for marker: %s' % (dye, marker))
            channel = assay.channels.filter( Channel.dye_id == EK._id( dye ) ).one()
            peaks = channel.find_peaks()
            estimated_peaks = peakutils.call_peaks( peaks, method_func )
            assigned_peaks = peakutils.analyze_peaks( estimated_peaks,
                    marker, 'undefined', marker_obj.min_size, method='allele-'+args.method )

            peaks_list.append( (assigned_peaks, channel) )

        all_peaks = [ x[0] for x in peaks_list ]
        peakutils.check_overlap_peaks( all_peaks )

        for (peaks, channel) in peaks_list:
            for ( value, size, peak, height, area, peak_type, marker_code,
                        method) in peaks:
                print('%4.3f\t%d\t%s\t%s' % (size, height, peak_type, marker_code))
            channel.assign_complete_peaks( peaks )

        print('Successfully analyzed assay %d out of %d' % (counter, len(assay_list)))
        sys.stdout.flush()
    print('Successfully importing %d assays' % counter)
    print('Commit database...')

