

from msaf.models import dbsession, Sample, Marker, Batch
from msaf.lib.analytics import SampleSet
from itertools import cycle
import yaml


def load_yaml(yaml_text):
    
    d = yaml.load( yaml_text )
    instances = {}
    for k in d:
        if k == 'selector':
            instances['selector'] = Selector.from_dict( d[k] )
        elif k == 'filter':
            instances['filter'] = Filter.from_dict( d[k] )
        elif k == 'differentiation':
            instances['differentiation'] = Differentiation.from_dict( d[k] )
        else:
            raise RuntimeError()

    return instances


def save_yaml( instances ):
    # we don't really need to save to YAML yet
    pass


colours = cycle( [ 'red', 'green', 'blue', 'orange', 'purple', 'black', 'magenta',
                    'wheat', 'cyan', 'brown', 'slateblue', 'lightgreen' ] )


class Selector(object):

    def __init__(self, samples = [], markers = []):
        self.samples = []
        self.markers = []

    @staticmethod
    def from_dict(d):
        selector = Selector()
        selector.samples = d['samples']
        selector.markers = d['markers']
        return selector

    def to_dict(self):
        return { 'samples': self.samples, 'markers': self.markers }


    @staticmethod
    def load(yaml_text):
        d = yaml.load( yaml_text )
        selector = Selector.from_dict( d )
        return selector

    def dump(self):
        d = self.to_dict()
        return yaml.dump( d )


    def get_sample_ids(self, db):
        """ return sample ids; db is SQLa dbsession handler """
        pass

    def get_marker_ids(self):
        """ return marker ids; db is SQLa dbsession handler """
        # self.markers is name
        markers = [ Marker.search(name) for name in self.markers ]
        return [ marker.id for marker in markers ]

    def get_sample_sets(self, db=None):

        if not db:
            db = dbsession
        
        sample_set = []
        for label in self.samples:

            if label == '__ALL__':
                # single query
                pass
            
            sample_ids = []

            sample_selector = self.samples[label]
            for spec in sample_selector:
                if 'query' in spec:
                    
                    if '$' in spec['query']:
                        raise RuntimeError('query most not an advance one')

                    if 'batch' in spec:
                        query = spec['batch'] + '[batch] & (' + spec['query'] + ')'

                elif 'codes' in spec:

                    batch = Batch.search(spec['batch'])
                    q = dbsession.query( Sample.id ).join( Batch ).filter( Batch.id == batch.id).filter( Sample.code.in_( spec['codes'] ) ) 

                    sample_ids += list( q )
                        

            if label == '__ALL__':
                label = '-'

            sample_set.append( SampleSet(   location = '', year = 0,
                                            label = label,
                                            colour = next(colours),
                                            sample_ids = sample_ids ) )

        return sample_set


class Filter(object):

    def __init__(self):
        self.abs_threshold = 0
        self.rel_threshold = 0
        self.rel_cutoff = 0
        self.sample_qual_threshold = 0
        self.marker_qual_threshold = 0
        self.sample_options = None

    @staticmethod
    def from_dict(d):
        filter_params = Filter()
        filter_params.abs_threshold = int( d['abs_threshold'] )
        filter_params.rel_threshold = float( d['rel_threshold'] )
        filter_params.rel_cutoff = float( d['rel_cutoff'] )
        filter_params.sample_qual_threshold = float( d['sample_qual_threshold'] )
        filter_params.marker_qual_threshold = float( d['marker_qual_threshold'] )
        filter_params.sample_option = d['sample_option']
        return filter_params


    def to_dict(self):
        pass


    @staticmethod
    def load(yaml_text):
        pass

    def dump(self):
        pass



class Differentiation(object):

    def __init__(self):
        self.spatial = 0
        self.temporal = 0
        self.differentiation = 0

    @staticmethod
    def from_dict(d):
        differentiation = Differentiation()
        differentiation.spatial = d['spatial']
        differentiation.temporal = d['temporal']
        differentiation.detection = d['detection']
        return differentiation


    def to_dict(self):
        pass

    @staticmethod
    def load(yaml_text):
        pass

    def dump(self):
        pass



def create_group( selector ):
    pass

