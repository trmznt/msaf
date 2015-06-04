__copyright__ = '''
msaf/lib/advquerycmd.py - part of MsAF

(c) 2014 - Hidayat Trimarsanto <anto@eijkman.go.id> / <trimarsanto@gmail.com>

All right reserved.
This software is licensed under GPL v3 or later version.
Please read the README.txt of this software.
'''

#
# Example queries:
# IDPV[batch] !! indonesia[country] >> Indonesia $ malaysia[country] >> Malaysia

from msaf.lib.analytics import SampleSet
from msaf.lib.querycmd import parse_querycmd
from itertools import cycle


def parse_advquerycmd( query ):
    """ parse advanced query
    """

    query = query.strip()
    colours = cycle( [ 'red', 'green', 'blue', 'orange', 'purple', 'black', 'magenta',
                    'wheat', 'cyan', 'brown', 'slateblue', 'lightgreen' ] )


    if '!!' not in query and '$' not in query:
        # use simple parse_querycmd
        sample_ids = parse_querycmd( query )

        return [ SampleSet( location='', year=0, label='-', sample_ids = sample_ids) ]


    if '!!' in query:
        if query.count('!!') != 1:
            raise RuntimeError('Operator !! should only exist once.')

        common_query, split_query = query.split('!!')

    else:
        common_query, split_query = None, query


    set_queries = split_query.split('$')

    sample_set = []

    for set_query in set_queries:

        querycmd, label = set_query.split('>>')

        if common_query:
            querycmd = common_query + querycmd

        sample_ids = parse_querycmd( querycmd )

        sample_set.append( SampleSet(   location='', year = 0,
                                        label=label,
                                        colour=next(colours),
                                        sample_ids = sample_ids ) )
        print("Creating sampleset with label %s and sample_ids = %d" % (label, sample_ids.count()))

    return sample_set


