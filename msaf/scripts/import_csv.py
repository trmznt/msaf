
import sys
from msaf.lib.jsonfmt import csv2json

def main(argv=sys.argv):

    infile = open(argv[1])
    outfile = open(argv[2], 'w')

    outfile.write( csv2json( infile, allele_column=3 ) )


if __name__ == '__main__':
    main()
