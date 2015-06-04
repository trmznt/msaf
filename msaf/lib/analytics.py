
from msaf.lib.queryfuncs import AlleleDF, SampleDF, query2list
from pandas import DataFrame, pivot_table
from sqlalchemy import orm
from itertools import cycle, filterfalse
from collections import defaultdict
from operator import itemgetter

import numpy as np
import pycountry
from pprint import pprint


def group_samples( sample_ids,
            spatial_differentiation = 0,
            temporal_differentiation = 0 ):

    """ return [ (label, sample_ids, country, time), ... ] """

    sample_df = SampleDF.get_by_sample_ids( sample_ids, spatial_differentiation )

    samples = {}   # group sets
    colours = cycle( [ 'red', 'green', 'blue', 'orange', 'purple', 'black', 'magenta',
                    'wheat', 'cyan', 'brown', 'slateblue', 'lightgreen' ] )

    for idx, sample_id, location, year, month in sample_df.itertuples():
        
        if temporal_differentiation == 1:
            tag = (location, year)
        elif temporal_differentiation == 3:
            quarter = 'Q1'
            if month >= 9:
                quarter = 'Q4'
            elif month >= 6:
                quarter = 'Q3'
            elif month >= 3:
                quarter = 'Q2'
            tag = (location, '%d %s' % (year, quarter)) 
        else:
            tag = (location, None)

        try:
            samples[tag].append( int(sample_id) )
        except KeyError:
            samples[tag] = [ int(sample_id) ]

    sets = []
    for tag in sorted(samples.keys()):
        (location, year) = tag
        sets.append( SampleSet( location, year, next(colours), samples[tag] ) )

    sets.sort( key = lambda x: x.get_label() )
    return (sets, sample_df)


def group_samples2( sample_sets,
            spatial_differentiation = 0,
            temporal_differentiation = 0,
            detection_differentiation = False):
    """ spatial differentiation:
            -1  No differentiation
            0   country
            1   admin level 1
            2   amdin level 2
        return [ (label, sample_ids, country, time), ... ]
    """

    sets = []
    sample_dfs = None
    colours = cycle( [ 'red', 'green', 'blue', 'orange', 'purple', 'black', 'magenta',
                    'wheat', 'cyan', 'brown', 'slateblue', 'lightgreen' ] )

    for sample_set in sample_sets:

        sample_df = SampleDF.get_by_sample_ids( sample_set.get_sample_ids(),
                spatial_differentiation )

        samples = {}   # group sets

        for idx, sample_id, location, year, month, passive_detection in sample_df.itertuples():
        
            if temporal_differentiation == 1:
                tag = (location, year)
            elif temporal_differentiation == 3:
                quarter = 'Q1'
                if month >= 9:
                    quarter = 'Q4'
                elif month >= 6:
                    quarter = 'Q3'
                elif month >= 3:
                    quarter = 'Q2'
                tag = (location, '%d %s' % (year, quarter)) 
            else:
                tag = (location, None)

            if detection_differentiation:
                (location, year) = tag
                tag = (location, year, passive_detection)

            try:
                samples[tag].append( int(sample_id) )
            except KeyError:
                samples[tag] = [ int(sample_id) ]


        for tag in sorted(samples.keys()):
            if detection_differentiation:
                (location, year, passive_detection) = tag
            else:
                (location, year) = tag
                passive_detection = None

            label = sample_set.get_label() if not (location or year) else ''

            if passive_detection is not None:
                extra_label = 'PD' if passive_detection else 'AD'
            else:
                extra_label = None

            sets.append( SampleSet( location, year, next(colours), samples[tag],
                    label = label, extra_label = extra_label ))



        if sample_dfs is None:
            sample_dfs = sample_df
        else:
            sample_dfs = sample_dfs.append( sample_df, ignore_index=True )

    sets.sort( key = lambda x: x.get_label() )
    return (sets, sample_dfs)


class SampleSet(object):

    def __init__(self, location = '', year = 0, colour = None, sample_ids = None,
                    label = None, extra_label = None):
        self.time = year
        self.location = location
        self.country = location.split('/',1)[0]
        if label is not None:
            self.label = label
        else:
            self.label = ''
        if self.time:
            self.label = self.label + '%s | %s' % (self.location, str(self.time))
        else:
            self.label = self.label + self.location
        self.label = self.label.strip()

        # if label is too long, abbreviated as necessarily

        if self.label.count('/') >= 2 and len(self.label) > 24:
            name_components = self.label.split('/')
            country_code = pycountry.countries.get(name=name_components[0].strip().capitalize()).alpha2
            abbr_components = []
            for component in name_components[1:-1]:
                abbr_components.append( ''.join((c[0].upper() for c in component.split())) )
            self.label = ' / '.join( list([country_code,] + abbr_components + [name_components[-1],]) )
        if extra_label:
            self.label += ' ' + extra_label

        self.colour = colour
        self.sample_ids = sample_ids


    def set_sample_ids( self, sample_ids ):
        self.sample_ids = sample_ids


    def get_sample_ids( self ):
        return self.sample_ids


    def get_country(self):
        return self.country


    def get_label(self):
        return self.label


    def get_colour(self, fmt=None):
        return self.colour


    def __len__(self):
        if type(self.sample_ids) == orm.Query:
            return self.sample_ids.count()
        else:
            return len(self.sample_ids)


    def get_analyticalset( self, marker_ids = None,
            allele_absolute_threshold = 0,
            allele_relative_threshold = 0,
            allele_relative_cutoff = 0,
            snapshot_id = None,
            unique=False):

        analytical_set = AnalyticalSet( sample_set = self,
                allele_df = AlleleDF.get_all_alleles(
                            sample_ids = self.sample_ids,
                            snapshot_id = snapshot_id,
                            marker_ids = marker_ids,
                            allele_absolute_threshold = allele_absolute_threshold,
                            allele_relative_threshold = allele_relative_threshold,
                            allele_relative_cutoff = allele_relative_cutoff),
                unique = unique )

        print("AnalyticalSet created for [%s] with [%d] samples" %
                ( self.get_label(), analytical_set.get_N() ) )
        
        if analytical_set.get_N() > 0:
            return analytical_set

        return None

    def filter_sampleids( self, sample_ids ):
        """ return a cloned SampleSet but only with sample_ids in sample_ids
        """

        self.sample_ids = query2list(self.sample_ids)
        filtered_sample_ids = list( set(self.sample_ids) & set(sample_ids) )

        ss = SampleSet( sample_ids = filtered_sample_ids )
        ss.location = self.location
        ss.country = self.country
        ss.time = self.time
        ss.label = self.label
        ss.colour = self.colour
        return ss


class AnalyticalSet(object):


    def __init__(self, sample_set = None, allele_df = None, unique = False, strict = False ):
        self.sample_set = sample_set
        self.sample_ids = None
        self.allele_df = allele_df
        self.dominant_allele_df = None
        self.marker_df = None
        self.marker_ids = None
        self.marker_distribution = None
        self.allele_summaries = None
        self.dominant_allele_summaries = None
        self.moi = None
        self.genotypes = None
        self.unique_genotypes = None
        self.flag_unique = unique
        self.flag_strict = strict


    def __repr__(self):
        return "<AnalyticalSet %s %d>" % (self.get_label(), len(self))

    def get_label(self):
        return self.get_sample_set().get_label()


    def get_colour(self, fmt=None):
        return self.get_sample_set().get_colour(fmt)


    def get_country(self):
        return self.get_sample_set().get_country()


    def get_sample_set(self):
        return self.sample_set


    def get_allele_df(self):
        return self.allele_df


    def get_marker_df(self):
        if self.marker_df is None:
            self.marker_df = pivot_table( self.get_allele_df(),
                    rows = 'sample_id', cols = 'marker_id', values='value', aggfunc = len )
        return self.marker_df


    def get_marker_ids(self):
        #unique_marker_df = self.allele_df.drop_duplicates( ['marker_id'] )
        #return [ int(e[1]) for e in unique_marker_df.itertuples() ]
        if self.marker_ids is None:
            if len(self.allele_df) > 0:
                self.marker_ids = [ int(x) for x in set( self.allele_df['marker_id'] ) ]
            else:
                self.marker_ids = []
        return self.marker_ids


    def get_sample_ids(self):
        if self.sample_ids is None:
            if len(self.allele_df) > 0:
                self.sample_ids = [ int(x) for x in set( self.allele_df['sample_id'] ) ]
            else:
                self.sample_ids = []
        return self.sample_ids


    def get_N(self):
        return len(self.get_sample_ids())


    def __len__(self):
        return self.get_N()


    def filter_sample_quality(self, sample_quality_threshold, marker_ids = None):
        sample_ids = {}
        failed_genotypes = []
        failed_samples = 0
        passed_sample_ids = []

        for (idx, marker_id, sample_id,
                allele, size, height, assay_id) in self.allele_df.itertuples():
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

        return failed_genotypes, failed_samples, AnalyticalSet( sample_set = self.sample_set,
            allele_df = self.allele_df[ self.allele_df['sample_id'].isin( passed_sample_ids )] )


    def get_marker_distribution(self):
        """ return dataframe of ( sample_id, marker1, marker2, ... ) with marker frequency """

        if self.marker_distribution is None:
        
            unique_marker_sample_df = self.allele_df.drop_duplicates(
                                                    ['marker_id', 'sample_id'] )
            self.marker_distribution = pivot_table( unique_marker_sample_df,
                            rows='marker_id', values='sample_id', aggfunc=len )

        return self.marker_distribution


    def filter_strict_samples(self):
        """ return analytical_set with strict samples, i.e. samples with only 1 locus
            with multiple alleles
        """
        moi = self.calculate_moi()
        return AnalyticalSet( sample_set = self.sample_set,
            allele_df = self.allele_df[ self.allele_df['sample_id'].isin(
                            [ k for k,v in moi.items() if v[1] <= 1] ) ] )


    def calculate_moi(self):
        """ calculate moi, returning { sample_id: ( moi, number of marker > 1 alleles ), } """

        if self.moi is None:
            marker_df = self.get_marker_df()
            self.moi = {}
            for item in marker_df.itertuples():
                self.moi[ int(item[0]) ] =  ( np.nanmax(item[1:] ),
                                    len( list( x for x in item[1:] if x > 1) ) )
                print(item[1:], ' -> ', self.moi[ int(item[0]) ])

        return self.moi


    def get_allele_summaries(self):
        """ return { 1: AlleleSummary, 2: AlleleSummary, ... } """

        if self.allele_summaries is None:

            allele_dists = defaultdict( lambda _=None: defaultdict(list) )
            sample_dists = defaultdict( lambda _=None: defaultdict(list) )
            for (idx, marker_id, sample_id, value, size, height, assay_id) in self.allele_df.itertuples():
                allele = (size, height)
                allele_dists[marker_id][value].append( allele )
                sample_dists[marker_id][sample_id].append( allele )

            self.allele_summaries = {}
            for marker_id in allele_dists:
                self.allele_summaries[marker_id] = AlleleSummary( allele_dists[marker_id],
                                                                sample_dists[marker_id] )

        return self.allele_summaries                


    def get_dominant_allele_summaries(self):
        """ similar to get_allele_summaries(), but just use dominant allele only """

        if self.dominant_allele_summaries is None:
            allele_dists = defaultdict( lambda _=None: defaultdict(list) )
            sample_dists = defaultdict( lambda _=None: defaultdict(list) )
            for (idx, marker_id, sample_id, value, size, height, assay_id) in self.get_dominant_alleles().itertuples():
                allele = (size, height)
                allele_dists[marker_id][value].append( allele )
                sample_dists[marker_id][sample_id].append( allele )

            self.dominant_allele_summaries = {}
            for marker_id in allele_dists:
                self.dominant_allele_summaries[marker_id] = AlleleSummary(
                                allele_dists[marker_id], sample_dists[marker_id] )
        return self.dominant_allele_summaries


    def get_dominant_allele_summaries(self):
        """ this works by getting the dominant genotype first, and then convert back
            to allele / sample list
        """

        if self.dominant_allele_summaries is None:
            sample_ids = None
            if self.flag_unique:
                genotypes = self.get_unique_genotypes()
                sample_ids = genotypes.index

            allele_dists = defaultdict( lambda _=None: defaultdict(list) )
            sample_dists = defaultdict( lambda _=None: defaultdict(list) )
            for (idx, marker_id, sample_id, value, size, height, assay_id) in self.get_dominant_alleles().itertuples():
                if self.flag_unique and sample_id not in sample_ids:
                    continue
                allele = (size, height)
                allele_dists[marker_id][value].append( allele )
                sample_dists[marker_id][sample_id].append( allele )

            self.dominant_allele_summaries = {}
            for marker_id in allele_dists:
                self.dominant_allele_summaries[marker_id] = AlleleSummary(
                                allele_dists[marker_id], sample_dists[marker_id] )
        return self.dominant_allele_summaries



    def get_He(self):
        allele_summaries = self.get_dominant_allele_summaries()
        marker_hes = [ s.get_He() for s in allele_summaries.values() ]
        #print('dominant allele summaries for %s' % self.get_label())
        #for k in allele_summaries:
        #    print('locus: %s' % k)
        #    pprint(allele_summaries[k].alleles)
        return sum( marker_hes ) / len( marker_hes )

    def get_marker_He(self):
        """ individual He for each markers """
        hes = {}
        allele_summaries = self.get_dominant_allele_summaries()
        for (marker_id, allele_summary) in allele_summaries.items():
            hes[marker_id] = allele_summary.get_He()

        return hes


    def get_moi_stats(self):
        """ return (mean, median, min, max, sd, prop, N)
        """
        moi = list( x[0] for x in self.calculate_moi().values() )
        print( self.get_label(), moi )
        N = len( list( filterfalse( lambda x: x <= 1, moi ) ) )

        return ( np.mean(moi), np.median(moi), min(moi), max(moi), np.std(moi), 
                N/len(moi), N )


    def get_dominant_alleles(self):
        """ return Pandas DataFrame of (marker_id, sample_id, value, size, height) """
        if self.dominant_allele_df is None: # error if checking by == None
            df = self.allele_df
            idx = df.groupby(['marker_id','sample_id'])['height'].transform(max) == df['height']
            self.dominant_allele_df = df[idx]
        return self.dominant_allele_df


    def get_genotypes(self):
        """ return Pandas Dataframe of (sample_id, value1, value2, value3, ...)
            this function DOES NOT drop NaN/na values
        """

        if self.genotypes is None:
            dominant_alleles = self.get_dominant_alleles()

            if len(dominant_alleles) == 0: 
                return DataFrame()

            genotypes = pivot_table( dominant_alleles,
                    rows = 'sample_id', cols = 'marker_id', values = 'value' )

            # check if genotypes length equals to marker_ids length, otherwise drop this set
            # otherwise, raise an inconsistency error!
            if len(genotypes.columns) != len(self.get_marker_ids()):
                raise RuntimeError( 'internal querying error in AnalyticalSet.get_genotypes()' )
            #if not na:
            #    self.genotypes = genotypes.dropna()
            self.genotypes = genotypes
        return self.genotypes


    def get_unique_genotypes(self, na = None):
        """ return Pandas Dataframe of unique (sample_id, value1, value2, value3, ...) """

        genotypes = self.get_genotypes()
        if len(genotypes) == 0:
            return []
        return genotypes.drop_duplicates()



class AlleleSummary(object):


    def __init__(self, alleles, samples = None):
        self.total = None
        self.total_height = None
        self.distribution = None
        self.moi = None
        self.alleles = alleles
        self.samples = samples


    def get_allelesf(self):
        return self.alleles


    def get_samples(self):
        return self.samples


    def get_unique(self):
        """ return number of unique alleles """
        return len(self.alleles)


    def get_total(self):
        """ return total number of alleles """

        if self.total is None:
            self.total = sum( self.get_distribution() )
        return self.total


    def get_total_height(self):
        """ return total rfu of all signals """

        if self.total_height is None:
            self.total_height = 0
            for alleles in self.alleles:
                for (size, height) in alleles:
                    self.total_height += height
        return self.total_height


    def get_distribution(self):
        """ return the allele distribution (frequencies) """

        if self.distribution is None:
            self.distribution = list( len(x) for x in self.alleles.values() )
        return self.distribution


    def get_moi_distribution(self):
        """ return moi distribution """
        if self.moi is None:
            self.moi = list( len(x) for x in self.samples.values() )
        return self.moi


    def average_height(self):
        return self.get_total_height() / self.get_total()


    def get_He(self, sample_adjustment = True):
        total = self.get_total()
        dist = self.get_distribution()
        he = 1.0 - sum( (x/total)**2 for x in dist )
        if sample_adjustment and total > 1:
            return 1.0 * total / (total - 1) * he
        return he


    def get_basic_stats(self):
        """ return mean, median, min, max, sd """

        dist = self.get_distribution()
        return ( np.mean( dist ), np.median( dist ), min( dist ), max( dist ), np.std( dist ) )


    def get_moi_stats(self):
        """ return mean, median, min, max, sd for multiplicity of infections """
        dist = self.get_moi_distribution()
        return ( np.mean( dist ), np.median( dist ), min( dist ), max( dist ), np.std( dist ) )


    def get_polyclonality(self):
        sample_dist = self.get_moi_distribution()
        return len(list(filterfalse(lambda x: x <= 1, sample_dist)))



# stand-alone functions

def get_sample_ids( analytical_sets ):

    sample_ids = set()
    for analytical_set in analytical_sets:
        sample_ids.update( analytical_set.get_sample_ids() )
    return sample_ids


def get_marker_ids( analytical_sets ):

    marker_ids = set()
    for analytical_set in analytical_sets:
        marker_ids.update( analytical_set.get_marker_ids() )
    return marker_ids


def get_labels( analytical_sets ):
    return [ s.get_label() for s in analytical_sets ]


def combine_allele_summaries(*allele_summaries):
    allele_total = defaultdict(list)
    sample_total = defaultdict(list)
    for allele_summary in allele_summaries:
        alleles = allele_summary.alleles
        samples = allele_summary.samples
        for allele in alleles:
            allele_total[allele].extend( alleles[allele] )
        for sample in samples:
            sample_total[sample].extend( samples[sample] )

    return AlleleSummary( allele_total, sample_total )


def get_main_country( sets ):
    """ find the main country of the dataset """
    countries = defaultdict( int )
    for s in sets:
        countries[ s.get_country() ] += len(s)

    country_list = sorted( countries.items(), key = itemgetter(1) )

    return country_list[-1][0]


def combine_analyticalsets( analytical_sets, country = None ):

    if country:
        country_sets = [ s for s in analytical_sets if s.get_sample_set().get_country() == country ]
    else:
        country_sets = analytical_sets

    allele_df = country_sets[0].get_allele_df()
    if len(country_sets) > 1:
        allele_df = allele_df.append( [ s.get_allele_df() for s in country_sets[1:] ],
                        ignore_index = True )

    return AnalyticalSet( SampleSet( location = country, year = None ), allele_df )


def get_haplotypes( analytical_sets, dropna = True ):
    """ na is set to True if we want haplotypes with na value,
        return a zip of [ (analytical_set, haplotypes), ... ]
    """

    if dropna:
        marker_len = max( len(x.get_marker_ids()) for x in analytical_sets )
        marker_label = None

    genotype_sets = []
    for s in analytical_sets:
        genotypes = s.get_genotypes()

        if dropna:
            genotypes = genotypes.dropna()
        
            if len(genotypes.columns) < marker_len:
                continue

            if marker_label is None:
                marker_label = genotypes.columns
            elif not (marker_label == genotypes.columns).all():
                raise RuntimeError('markers are different across analytical sets')

        if len(genotypes) == 0:
            continue

        genotype_sets.append( (s, genotypes) )

    return genotype_sets

get_genotypes = get_haplotypes


class ClonalitySummary(object):

    def __init__(self):
        self.samples = defaultdict(int)

    def combine(self, samples):
        for (k,v) in samples.items():
            self.samples[k] = max( self.samples[k], len(v) )

    def polyclonality(self):
        n = 0
        for v in self.samples.values():
            if v > 1: n += 1
        return n

    def __len__(self):
        return len(self.samples)

