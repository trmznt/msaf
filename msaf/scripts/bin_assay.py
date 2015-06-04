
import sys, os, io
import argparse
import transaction
from msaf.lib.microsatellite import peakutils3 as peakutils
from msaf.models import Allele, AlleleSet, Sample, Batch, Marker, EK, dbsession


def init_argparser():

    parser = argparse.ArgumentParser( "" )

    parser.add_argument('--batch', required=True,
                help = 'batch code' ),
    parser.add_argument('--markers', required=True,
                help = 'marker codes' ),
    parser.add_argument('--user', '-u',
                help = 'user name' )

    return parser


def main(args):

    with transaction.manager:
        bin_assay( args )

    print('Done!')


def bin_assay( args ):

    markers = args.markers.split(',')
    batch = Batch.search( args.batch )
    if not batch:
        raise RuntimeError('Batch code: %s does not exist' % args.batch)

    samples = Sample.query().join( Batch ).filter( Batch.id == batch.id )
    print('Batch %s has %d samples' % (batch.code, samples.count()))

    for marker_code in markers:
        marker = Marker.search(marker_code)
        repeats = marker.repeats
        bins = marker.bins

        print('Marker: %s' % marker.code)
        print('Bins:', bins)

        for sample in samples:

            q = Allele.query().join( AlleleSet ).join( Sample )
            q = q.filter( Sample.id == sample.id )
            q = q.filter( Allele.marker_id == marker.id )

            print('Sample code: %s' % sample.code)
            for allele in q:
                print('Bin: %d size: %3.2f' % (allele.value, allele.size))

            peakutils.bin_peaks( q, bins, 1.0 * repeats / 2 )

            dbsession.flush()

    
