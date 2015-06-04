
#from msaf.models import *
from plasmoms.models import *
from msaf.lib.querycmd import parse_querycmd

from sqlalchemy import extract
from sqlalchemy.orm import aliased
from pandas import DataFrame, pivot_table

from itertools import cycle


class SampleID(object):
    """ return sample_ids either as list or as sqlalchemy query session """

    @staticmethod
    def get_by_batchcode( batchcode ):

        batch = Batch.search( batchcode )
        if not batch:
            return RuntimeError('Batch code does not exist: %s' % batchcode)

        return dbsession.query(Sample.id).filter( Sample.batch_id == batch_id )


class SampleDF(object):
    """ return a Pandas dataframe of | sample_id, location, year |"""

    @staticmethod
    def get_by_sample_ids( sample_ids, location_level = 4, class_ = PlasmoSample ):

        q = dbsession.query( class_.id, class_.location_id,
                        extract('year', class_.collection_date),
                        extract('month', class_.collection_date),
                        class_.passive_case_detection
            ).filter( class_.id.in_( sample_ids ) )

        df = DataFrame([ (sample_id, Location.get(location_id).render(level=location_level),
                        year, month, passive_detection)
                        for (sample_id, location_id, year, month, passive_detection) in q ])

        if len(df) != 0:
            df.columns = ( 'sample_id', 'location', 'year', 'month', 'passive_detection' )

        return df


class AlleleDF(object):
    """ return a Pandas dataframe of marker_id, sample_id, value, size, height """

    @staticmethod
    def get_all_alleles( sample_ids, marker_ids = None,
            allele_absolute_threshold = 0, allele_relative_threshold = 0,
            allele_relative_cutoff = 0,
            peak_type = 'peak-bin',
            snapshot_id = None ):

        q = dbsession.query( AlleleSet.sample_id, AlleleSet.marker_id,
                Allele.value, Allele.size, Allele.height,
                Channel.assay_id ).join( Allele ).join( Channel )
        q = q.filter( AlleleSet.sample_id.in_( sample_ids ) )

        # set the peak types
        #q = q.filter( Allele.type_id.in_( [ EK._id(x) for x in peak_types ] ) )
        if type(peak_type) in [ list, tuple ]:
            q = q.filter( Allele.type_id.in_( EK.getids( peak_type ) ) )
        else:
            q = q.filter( Allele.type_id == EK.getid(peak_type) )

        # we order based on marker_id, sample_id and then descending height
        q = q.order_by( AlleleSet.marker_id, AlleleSet.sample_id, Allele.height.desc() )

        print('MARKER IDS:', marker_ids)

        if marker_ids:
            q = q.filter( AlleleSet.marker_id.in_( marker_ids ) )
            #q = q.outerjoin( Marker, Allele.marker_id == Marker.id )
            #q = q.filter( Marker.id.in_( marker_ids ) )

        if allele_absolute_threshold > 0:
            q = q.filter( Allele.height > allele_absolute_threshold )

        if allele_relative_threshold == 0 and allele_relative_cutoff == 0:
            df = DataFrame( [ (marker_id, sample_id, value, size, height, assay_id )
                    for ( sample_id, marker_id, value, size, height, assay_id ) in q ] )

        else:

            alleles = []

            max_height = 0
            last_marker_id = 0
            last_sample_id = 0
            skip_flag = False
            for sample_id, marker_id, value, size, height, assay_id in q:
                if sample_id == last_sample_id:
                    if last_marker_id == marker_id:
                        if skip_flag:
                            continue
                        ratio = height / max_height
                        if ratio < allele_relative_threshold:
                            continue
                        if allele_relative_cutoff > 0 and ratio > allele_relative_cutoff:
                            # turn off this marker by skipping this sample_id & marker_id
                            skip_flag = True
                            # don't forget to remove the latest allele
                            del alleles[-1]
                            continue
                            
                else:
                    last_sample_id = sample_id
                    last_marker_id = marker_id
                    max_height = height
                    skip_flag = False

                alleles.append( (marker_id, sample_id, value, size, height, assay_id) )

            df = DataFrame( alleles )
        
        if len(df) == 0:
            return df

        df.columns = ( 'marker_id', 'sample_id', 'value', 'size', 'height', 'assay_id' )
        return df

    @staticmethod
    def get_dominant_alleles( sample_ids, marker_ids = None ):

        t1 = aliased( Allele )
        t2 = aliased( Allele )
        s1 = aliased( AlleleSet )
        marker_ids = [ int(x) for x in marker_ids ]

        # I honestly forgot how the mundane thing below works !!!
        # I was smarter when I was younger 8-(
        q = dbsession.query( t1.marker_id, s1.sample_id, t1.value, t1.size, t1.height ).\
            join( s1 ).\
            outerjoin( t2, and_( t1.marker_id == t2.marker_id,
                                t1.alleleset_id == t2.alleleset_id,
                                t1.height < t2.height) ).\
            filter( t2.marker_id == None ).order_by( t1.marker_id, s1.sample_id ).\
            filter( s1.sample_id.in_( sample_ids ) ).filter( t1.marker_id.in_( marker_ids ))

        df = DataFrame( [ (marker_id, sample_id, value, size, height)
                        for marker_id, sample_id, value, size, height in q ] )

        if len(df) == 0:
            return None

        df.columns = ( 'marker_id', 'sample_id', 'value', 'size', 'height' )
        return df.drop_duplicates( ['marker_id', 'sample_id'] )

    @staticmethod
    def get_by_snapshot( snapshot_id, marker_ids = None ):
        pass

MarkerDF = AlleleDF


class AlleleSummary(object):

    def __init__(self, marker):
        # contain sample_id: no_of_alleles
        self.marker = marker
        self.samples = {}
        self.total = 0
        self.total_height = 0
        self.alleles = {}

    def unique_alleles(self):
        return len(self.alleles)

    def total_alleles(self):
        return self.total

    def average_height(self):
        return self.total_height / self.total

    def He(self, sample_adjustment = False):
        he = 1.0 - sum( (len(self.alleles[i])/self.total)**2 for i in self.alleles )
        if sample_adjustment:
            return 1.0 * self.total / (self.total - 1) * he
        return he


def generate_allele_summary(df):
    """ return a list of marker summary """

    summaries = []
    
    last_marker_id = -1
    curr_summary = None

    for (index, ( marker_id, sample_id, value, size, height )) in df.iterrows():

        if marker_id != last_marker_id:
            last_marker_id = marker_id
            curr_summary = AlleleSummary( Marker.get(marker_id).code )
            summaries.append( (marker_id, curr_summary) )

        if sample_id in curr_summary.samples:
            curr_summary.samples[sample_id] += 1
        else:
            curr_summary.samples[sample_id] = 1

        curr_summary.total += 1
        curr_summary.total_height += height

        try:    
            curr_summary.alleles[value].append( (size, height) )
        except KeyError:
            curr_summary.alleles[value] = [ (size, height) ]


    results = []
    # return results as: marker, unique_alleles, total_alleles, mean, median, range
    # of allele per sample, mean, median, range of signal height, He
    for (marker_id, summary) in summaries:

        results.append(
            (   summary.marker,
                summary.unique_alleles(), summary.total_alleles(),
                0.0, 0.0, 0.0,
                0.0, 0.0, 0.0, summary.He() )
        )

    results.sort()

    return results


def query2list( ids ):
    if type(ids) == list:
        return ids
    return [ e[0] for e in ids ]


class AnalyticalSet(object):

    def __init__(self, sample_ids, marker_ids = None,
            absolute_threshold = 0, relative_threshold = 0, quality_threshold = 1,
            snapshot_id = None, label = '', colour = None):
        """
        AnalyticalUnit
            @@sample_ids: either a list or an SqlAlchemy query object
            @@marker_ids: either a list or an SqlAlchemy query object

        """

        if type(sample_ids) == list:
            self.sample_ids = sample_ids
        else:
            self.sample_ids = [ e[0] for e in sample_ids ]

        if type(marker_ids) == list:
            self.marker_ids = marker_ids
        else:
            self.marker_ids = [ e[0] for e in marker_ids ]


        self.absolute_threshold = int(absolute_threshold)
        self.relative_threshold = float(relative_threshold)
        self.quality_threshold = float(quality_threshold)
        self.snaphost_id = snapshot_id
        self.label = label
        self.colour = colour

        # allele df is Pandas DataFrame of (marker_id, sample_id, value, size, height)

        self.allele_df = AlleleDF.get_all_alleles(
                self.sample_ids, self.marker_ids,
                self.absolute_threshold,
                self.relative_threshold
            )

        self.dominant_allele_df = None


    def get_allele_summary(self):
        pass


    def alleles(self):
        """ return Pandas DataFrame of (marker_id, sample_id, value, size, height) """
        return self.allele_df


    def dominant_alleles(self):
        """ return Pandas DataFrame of (marker_id, sample_id, value, size, height) """
        if self.dominant_allele_df is None: # error if checking by == None
            _ = self.allele_df
            idx = _.groupby(['marker_id', 'sample_id'])['height'].transform(max) == _['height']
            self.dominant_allele_df = _[idx]
        return self.dominant_allele_df


    def get_dominant_genotypes(self):
        """ return Pandas Dataframe of (sample_id, value1, value2, value3, ...) """
        dominant_alleles = self.dominant_alleles()

        if len(dominant_alleles) == 0: 
            return []

        genotypes = pivot_table( dominant_alleles,
                rows = 'sample_id', cols = 'marker_id', values = 'value' )

        # check if genotypes length equals to marker_ids length, otherwise drop this set
        if len(genotypes.columns) != len(self.marker_ids):
            return []
        return genotypes.dropna()


    def get_unique_dominant_genotypes(self):
        """ return Pandas Dataframe of unique (sample_id, value1, value2, value3, ...) """

        genotypes = self.get_dominant_genotypes()
        if len(genotypes) == 0:
            return []
        return genotypes.drop_duplicates()


    def get_mcc_genotypes(self):
        raise NotImplemented


    def get_ld(self):
        pass


    def __len__(self):
        return len(self.sample_ids)


class SampleSet(object):

    def __init__(self, location, year, colour=None, sample_ids = None):
        self.time = year
        self.location = location
        self.country = location.split('/',1)[0]
        if self.time:
            self.label = '%s | %d' % (self.location, self.time)
        else:
            self.label = self.location
        self.colour = colour
        self.sample_ids = sample_ids


    def set_sample_ids( self, sample_ids ):
        self.sample_ids = sample_ids


    def get_sample_ids( self ):
        return self.sample_ids


    def get_analyticalset( self, marker_ids = None,
            allele_absolute_threshold = 0,
            allele_relative_threshold = 0,
            snapshot_id = None):

        analytical_set = AnalyticalSet2( sample_set = self,
                allele_df = AlleleDF.get_all_alleles(
                            sample_ids = self.sample_ids,
                            snapshot_id = snapshot_id,
                            marker_ids = marker_ids,
                            allele_absolute_threshold = allele_absolute_threshold,
                            allele_relative_threshold = allele_relative_threshold ) )

        return analytical_set


class AnalyticalSet2(object):

    def __init__(self, sample_set = None, allele_df = None ):
        self.sample_set = sample_set
        self.allele_df = allele_df


    def get_marker_ids(self):
        #unique_marker_df = self.allele_df.drop_duplicates( ['marker_id'] )
        #return [ int(e[1]) for e in unique_marker_df.itertuples() ]
        return [ int(x) for x in set( self.allele_df['marker_id'] ) ]


    def get_sample_ids(self):
        #unique_sample_df = self.allele_df.drop_duplicates( ['sample_id'] )
        return [ int(x) for x in set( self.allele_df['sample_id'] ) ]


    def filter_sample_quality(self, sample_quality_threshold, marker_ids = None):
        sample_ids = {}
        failed_genotypes = []
        failed_samples = 0
        passed_sample_ids = []

        for idx, marker_id, sample_id, allele, size, height in self.allele_df.itertuples():
            if marker_ids:
                if marker_id not in marker_ids:
                    continue
            try:
                sample_ids[sample_id].add( marker_id )
            except KeyError:
                sample_ids[sample_id] = { marker_id }

        n = len(marker_ids)
        max_failed = n - sample_quality_threshold * n

        for sample_id, markers in sample_ids.items():
            failed_allele = n - len(markers)
            failed_genotypes.append( failed_allele )
            if failed_allele > max_failed:
                failed_samples += 1
            else:
                passed_sample_ids.append( sample_id )

        return failed_genotypes, failed_samples, AnalyticalSet2( sample_set = self.sample_set,
            allele_df = self.allele_df[ self.allele_df['sample_id'].isin( passed_sample_ids )] )


    def filter_marker_quality(self, marker_quality_threshold, marker_ids = None):
        
        unique_marker_sample_df = self.allele_df.drop_duplicates( ['marker_id', 'sample_id'] )
        markers = {}
        for idx, marker_id, sample_id in unique_marker_sample_df.itertuples():
            if marker_ids:
                if marker_id not in marker_ids:
                    continue
            try:
                markers[marker_id] += 1
            except KeyError:
                markers[marker_id] = 1

        return [ (k, len(v)) for k, v in markers.items() ]

        

def group_samples( sample_ids,
            spatial_differentiation = 0,
            temporal_differentiation = 0,
            custom_differentiation = None):
    """
        return [ (label, sample_ids, country, time), ... ]
    """

    sample_df = SampleDF.get_by_sample_ids( sample_ids, spatial_differentiation )

    samples = {}   # group sets
    colours = cycle( [ 'red', 'green', 'blue', 'orange', 'purple', 'yellow', 'black', 'magenta',
                    'wheat', 'cyan', 'brown', 'slateblue' ] )

    for idx, sample_id, location, year in sample_df.itertuples():
        
        if temporal_differentiation == 1:
            tag = (location, year)
        else:
            tag = (location, None)

        try:
            samples[tag].append( int(sample_id) )
        except KeyError:
            samples[tag] = [ int(sample_id) ]

    sets = []
    for tag in samples:
        (location, year) = tag
        sets.append( SampleSet( location, year, next(colours), samples[tag] ) )
    return sets


def get_countries( sample_sets ):

    countries = {}
    for sample_set in sample_sets:
        pass

    return countries
        
    
