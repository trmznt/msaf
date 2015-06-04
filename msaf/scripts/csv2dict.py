
import sys
import argparse
from msaf.lib.dictfmt import csv2dict


def arg_parser():

    parser = argparse.ArgumentParser( "convert CSV to JSON" )

    parser.add_argument('--assay-only', action='append_const', dest = 'opts',
                const = 'assay-only',
                help = 'only create assay information')
    parser.add_argument('--fmt', choices=['json', 'yaml'])
    parser.add_argument('infile')
    parser.add_argument('outfile')

    return parser


def main(argv=sys.argv):

    parser = arg_parser()

    args = parser.parse_args()

    print("Reading %s" % args.infile)
    infile = open( args.infile )
    d, report = csv2dict(infile)


    print("Writing to %s" % args.outfile)
    outfile = open( args.outfile, 'w' )

    if args.fmt == 'json':
        import json
        outfile.write( json.dumps( d ) )
    elif args.fmt == 'yaml':
        import yaml
        yaml.safe_dump_all( d, outfile, default_flow_style=False )


if __name__ == '__main__':
    main()
    
