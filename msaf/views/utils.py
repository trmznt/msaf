import logging

log = logging.getLogger(__name__)

from msaf.models import dbsession, EK, Marker
from msaf.lib.querycmd import get_queries
from msaf.lib.queryutils import load_yaml

from operator import itemgetter, attrgetter


def get_marker_list(species=None):
    """ return a list of [ ('marker code', id), ... ] sorted by marker code """

    q = Marker.query()

    if species:
        q = q.filter( Marker.species_id == EK._id(species) )

        markers = [ ( '%s/%s' % (species, m.code), m.id ) for m in q ]
        
    else:
        markers = [ ( m.id, m.code ) for m in q ]

    markers.sort( key = itemgetter(1) )
    markers.insert(0, (-1, '*'))

    return markers


class BaseParameters(object):
    """ base parameters """

    def __init__(self):
        self.batches = None
        self.queryset = None
        self.marker_ids = None
        self.allele_absolute_threshold = 0
        self.allele_relative_threshold = 0
        self.allele_relative_cutoff = 0
        self.sample_quality_threshold = 0
        self.marker_quality_threshold = 0
        self.unique = False
        self.strict = False


def parse_base_params( d, exclude = None ):
    """ d: dictionary """

    p = BaseParameters()
    p.batch = d.get('batchcode', None)
    p.queryset = d.get('queryset', '').strip()
    if not exclude or 'marker' not in exclude:
        p.marker_ids = [ int(x) for x in d.getall('markers') ]
    p.allele_absolute_threshold = int(d.get('allele_absolute_threshold', 100))
    p.allele_relative_threshold = float(d.get('allele_relative_threshold', 0.33))
    p.allele_relative_cutoff = float(d.get('allele_relative_cutoff', 0))
    p.sample_quality_threshold = float(d.get('sample_quality_threshold', 0.50))
    p.marker_quality_threshold = float(d.get('marker_quality_threshold', 0.10))
    sample_option = d.get('sample_option', 'A')
    if sample_option == 'S':
        p.strict = True
    elif sample_option == 'U':
        p.unique = True

    if p.batch:
        if p.queryset:
            p.queryset = p.batch + '[batch] & (' + p.queryset + ')'
        else:
            p.queryset = p.batch + '[batch]'

    return p


def set_base_params( selector, filter ):
    """ given selector and filter, create BaseParameters instance """

    p = BaseParameters()
    p.marker_ids = selector.get_marker_ids()
    p.allele_absolute_threshold = filter.abs_threshold
    p.allele_relative_threshold = filter.rel_threshold
    p.allele_relative_cutoff = filter.rel_cutoff
    p.sample_quality_threshold = filter.sample_qual_threshold
    p.marker_quality_threshold = filter.marker_qual_threshold
    sample_option = filter.sample_option
    if sample_option == 'S':
        p.strict = True
    elif sample_option == 'U':
        p.unique = True

    return p

def parse_yaml_params( d ):
    yaml_text = d['yaml_ctrl']
    params = load_yaml( yaml_text )
    print(params)
    return (params['samples'], params['parameters'], params['differentiation'])
