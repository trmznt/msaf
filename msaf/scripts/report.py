# report
# command-line utility to create report

import sys, os, io, csv
import argparse, transaction
from msaf.scripts.fautil import get_assay_list


def init_argparser():

    parser = argparse.ArgumentParser( 'reporting module' )

    parser.add_argument('--batch', required=False, default = '',
        help = 'batch code')
    parser.add_argument('--query', required=False, default = '',
        help = 'query text')
    parser.add_argument('--assay', required=False, default = '',
        help = 'assay code')
    parser.add_argument('--sample', required=False, default = '',
        help = 'sample code')
    parser.add_argument('--marker', required=False, default = '',
        help = 'marker code(s)')

    parser.add_argument('--scanoverlap', required=False, action='store_true', default=False,
        help = 'scan overlapping peaks that may be real peaks')

    parser.add_argument('--relative_rfu', required=False, type=float, default=0.33,
        help = 'relative rfu height from the major peak')

    return parser


def main(args):

    do_report( args )


def do_report( args ):

    if args.scanoverlap:
        do_scanoverlap( args )

    print('Do nothing??')


def do_scanoverlap( args ):
    """ basically, this scan a particular assay for looking into any peak-overlaps which
        have higher height than peak-bin
    """
    
    assay_list = get_assay_list( args )

    for assay, sample_code in assay_list:

        print('Checking assay [%s] for sample [%s]...' % ( assay.filename, sample_code))
        
        for channel in assay.channels:
            alleles = channel.alleles

            bins = [ al for al in alleles if al.type == 'peak-bin' ]
            overlaps = [ al for al in alleles if al.type == 'peak-overlap' ]

            if len(overlaps) == 0:  
                continue

            if len(bins) == 0:
                if channel.marker.code != 'undefined':
                    print('=> WARNING: marker [%s] does not have any bins'
                                % channel.marker.code )
                continue

            bins.sort( key = lambda a: a.height, reverse = True )
            max_height = bins[0].height
            bins = [ al for al in bins if al.height > args.relative_rfu * max_height ]

            overlaps.sort( key = lambda a: a.height, reverse = True )

            if overlaps[0].height > bins[-1].height:
                print('=> Assay [%s] marker [%s] have overlaps' 
                            % (assay.filename, channel.marker.code))


