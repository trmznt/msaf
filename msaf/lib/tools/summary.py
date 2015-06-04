
from pandas import pivot_table
from msaf.models import *
from msaf.lib.queryfuncs import SampleDF, MarkerDF, AlleleDF, AnalyticalSet
from msaf.lib.analytics import ( group_samples, combine_allele_summaries,
                get_main_country, combine_analyticalsets, ClonalitySummary, group_samples2 )
import numpy as np

from msaf.lib.tools.genotype import dominant_genotypes
from msaf.lib.tools.distance import pw_distance, pca_distance
from msaf.lib.tools.lian import run_lian
from msaf.lib.tools.arlequin import run_arlequin, standardized_fst

from sqlalchemy import orm
from operator import itemgetter
import functools


class xxx_AlleleSummary(object):

    def __init__(self, marker):
        # contain sample_id: no_of_alleles
        self.marker = marker
        self.samples = {}
        self.total = 0
        self.total_height = 0
        self.frequencies = []
        self.alleles = {}

    def summarize(self):
        self.he = self.He()
        self.aps_mean, self.aps_median, self.aps_min, self.aps_max = self.calculate_aps()
        self.frequencies = self.calculate_frequencies()

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

    def calculate_aps(self):
        """ calculate aps: allele per sample """
        aps = list(self.samples.values())
        aps.sort()
        return np.mean( aps ), np.median( aps ), min( aps ), max( aps )

    def calculate_frequencies(self):
        frequencies = []
        for (k, v) in self.alleles.items():
            n = len(v)
            e0 = list( e[0] for e in v )
            e1 = list( e[1] for e in v )
            min_size = min( e0 )
            max_size = max( e0 )
            delta_size = max_size - min_size
            frequencies.append( (
                k, n, n/self.total,
                sum( e0 )/n,
                min_size,
                max_size,
                delta_size
            ) )
        frequencies.sort( key = lambda x: x[1], reverse=True )
        return frequencies


def xxx_generate_allele_summary(df):
    """ return a list of allele summary
        df := AlleleDF instance
    """

    summaries = []

    # sanity check
    if df is None or len(df) == 0:
        return summaries
    
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

    for (m, s) in summaries:
        s.summarize()

    return summaries


def report_by_location( df ):
    """ return pandas dataframe of | location, sample_id | """
    return pivot_table( df, rows='location', values='sample_id', aggfunc=len)


def report_by_year( df ):
    """ return pandas dataframe of | (year, location), sample_id | """
    return pivot_table( df, rows=['year', 'location'], values = 'sample_id', aggfunc=len)


def xxx_report_by_marker( df ):
    unique_sample_df = df.drop_duplicates( ['marker_id', 'sample_id'] )
    return pivot_table( unique_sample_df, rows='marker_id', values='sample_id', aggfunc=len)


def xxx_get_marker_ids( allele_df ):
    """ return [ marker_id, ... ] from allele_df """
    unique_marker_df = allele_df.drop_duplicates( ['marker_id'] )
    return [ int(e[1][0]) for e in unique_marker_df.iterrows() ]


def xxx_report_marker_quality( table, sample_size ):
    """ table is result of report_by_marker
        row := code, id, failed, proportion_failed, included
    """

    result = []

    for marker_id, sample_N in table.iteritems():
        marker = Marker.get( marker_id )
        failed_marker = sample_size - sample_N
        prop_failed_marker = failed_marker / sample_size
        result.append( (marker.code, marker.id, failed_marker, prop_failed_marker,
                True if prop_failed_marker < 0.1 else False ) )

    result.sort()
    return result


def xxx_group_sample_by_location( sample_df, base_country = True ):

    locations = {}
    for e in sample_df.itertuples():
        try:
            locations[e[2]].append( int(e[1]) )
        except KeyError:
            locations[e[2]] = [ int(e[1]) ]

    # assume that the local country is biggest sample
    countries = {}
    for l in locations:
        country = l.split(' / ', 1)[0]
        try:
            countries[country].extend( locations[l] )
        except:
            countries[country] = []
            countries[country].extend(locations[l])

    N = [ (len(countries[c]), c) for c in countries ]
    N.sort()
    if base_country:
        locations[N[-1][1]] = countries[N[-1][1]]

    return locations


def xxx_group_sample_by_differentiation( sample_ids, differentiation_method ):
    """ return [ (label, sample_ids, country) ] """

    l = []

    if differentiation_method < 0:
        # just create a single AnalyticalUnit
        l.append( ('ALL', 'ALL', sample_ids) )

    if differentiation_method == 0:
        # differentiated by year
        pass

    else:
        # differentiated by location level
        sample_df = SampleDF.get_by_sample_ids( sample_ids, differentiation_method )
        locations = group_sample_by_location( sample_df, base_country=False )
        for e in locations:
            l.append( (e, locations[e], e.split(' / ',1)) )
        l.sort()
    return l




def xxx_generate_analyticalsets( sample_groups, marker_ids,
        absolute_threshold = 0, relative_threshold = 0, quality_threshold = 0.5 ):

    units = []
    colours = [ 'red', 'green', 'blue', 'orange', 'purple', 'yellow', 'black', 'magenta',
                    'wheat', 'cyan', 'brown', 'slateblue' ]
    c = 0
    for g in sample_groups:
        units.append( AnalyticalSet( sample_ids = g[1], marker_ids = marker_ids,
                label = g[0], colour = colours[c],
                absolute_threshold = absolute_threshold,
                relative_threshold = relative_threshold,
                quality_threshold = quality_threshold ) )
        c += 1
    return units


def xxx_report_sample_quality( sample_locations, marker_quality_table, threshold = 0.5 ):

    results = []
    marker_ids = [ e[1] for e in marker_quality_table ]
    n = len(marker_ids)
    max_failed = n - threshold * n
    for (location, sample_ids) in sample_locations.items():
        failed_genotypes = []
        failed_samples = 0
        for sample_id in sample_ids:
            sample = Sample.get(sample_id)
            alleles = sample.get_alleles( marker_ids )
            failed_alleles = n - len(alleles)
            failed_genotypes.append( failed_alleles )
            if failed_alleles > max_failed:
                failed_samples += 1

        results.append( (location, failed_genotypes, failed_samples) )

    results.sort()
    return results


def xxx_report_sample_quality_from_allele_df( sample_locations, marker_ids, allele_df ):

    results = []
    n = len(marker_ids)

    return results


def xxx_filter_sample( sample_ids, marker_ids, threshold = 0.5 ):
    """ given a list of sample_id and marker_id, determine which sample_id that
        pass the quality above the given threshold
    """

    sample_ids = [ e[0] for e in sample_ids ]

    n = len(marker_ids)
    filtered_sample_ids = []
    for sample_id in sample_ids:
        sample = Sample.get(sample_id)
        alleles = sample.get_alleles( marker_ids )
        if len(alleles) > threshold * n:
            filtered_sample_ids.append( sample_id )

    return filtered_sample_ids


def xxx_filter_allele_df( allele_df, marker_ids = None,
                sample_quality_threshold = 0,
                allele_absolute_threshold = 0,
                allele_relative_threshold = 0,
                report = None ):

    """ given allele_df, return a filtered sample_df """


    if marker_ids is None:
        marker_ids = get_marker_ids( allele_df )

    if sample_quality_threshold:
        pass

    pass


def xxx_generate_location_summary( sample_locations, marker_quality_table ):
    """ calculate mean, median, range, % polyclonal, He and LDs """

    results = []
    marker_ids = [ int(e[1]) for e in marker_quality_table ]
    n = len(marker_ids)
    all_strict_sample_ids = []
    for (location, sample_ids) in sample_locations.items():

        sample_ids = [ int(x) for x in sample_ids ]
        
        # sample_moi
        sample_moi = []
        strict_sample_ids = []
        for sample_id in sample_ids:
            sample = Sample.get(sample_id)
            alleles = sample.get_alleles( marker_ids )
            if not alleles:
                continue
            sample_moi.append( max( [ len(x[1]) for x in alleles ] ) )

            if sum( [1 if len(x[1]) > 1 else 0 for x in alleles ] ) <= 1:
                strict_sample_ids.append( sample_id )

        polyclonal = 0
        sample_moi.sort()
        for moi in sample_moi:
            if moi > 1:
                polyclonal += 1

        # He
        markers = generate_allele_summary( AlleleDF.get_dominant_alleles(sample_ids, marker_ids ) )
        he = sum( m[1].He() for m in markers ) / n
        genotypes = dominant_genotypes( sample_ids, 0, marker_ids )
        unique_genotypes = genotypes.drop_duplicates()

        lian_result = run_lian( genotypes )
        lian_result_strict = run_lian( dominant_genotypes( strict_sample_ids, 0, marker_ids ) )
        lian_result_unique = run_lian( unique_genotypes )


        if not lian_result:
            continue

        results.append( ( location,
                        len( sample_moi ),
                        np.mean( sample_moi ),
                        np.median( sample_moi ),
                        min( sample_moi ),
                        max( sample_moi ),
                        polyclonal,
                        he,
                        lian_result.get_LD(),
                        lian_result.get_pvalue(),
                        len(strict_sample_ids),
                        lian_result_strict.get_LD() if lian_result_strict else 0,
                        lian_result_strict.get_pvalue() if lian_result_strict else 0,
                        len(unique_genotypes),
                        lian_result_unique.get_LD(),
                        lian_result_unique.get_pvalue() )
        )

        all_strict_sample_ids.extend( strict_sample_ids )

    results.sort()
    return results, all_strict_sample_ids


def xxx_generate_comprehensive_summary( sample_ids, location_level = 2, threshold=0 ):
    """ generate a comprehensive summary of sample collection """

    d = {}
    
    sample_df = SampleDF.get_by_sample_ids( sample_ids, location_level )

    d['sample_size'] = sample_ids.count()
    d['sample_dataframe'] = sample_df
    d['locations'] = report_by_location( sample_df )
    d['years'] = report_by_year( sample_df )

    marker_df = MarkerDF.get_all_alleles( sample_ids )

    d['markers'] = report_by_marker( marker_df )
    d['marker_quality'] = report_marker_quality( d['markers'], d['sample_size'] )

    d['sample_by_locations'] = group_sample_by_location( sample_df )

    d['sample_quality'] = report_sample_quality( d['sample_by_locations'], d['marker_quality'] )


    filtered_sample_ids = filter_sample( sample_ids, [ m[1] for m in d['marker_quality'] ] )
    filtered_sample_df = SampleDF.get_by_sample_ids( filtered_sample_ids,
                        location_level = location_level )
    filtered_marker_df = MarkerDF.get_all_alleles( filtered_sample_ids )

    d['filtered_sample_size'] = len(filtered_sample_ids)

    d['filtered_markers'] = report_by_marker( filtered_marker_df )
    d['filtered_marker_quality'] = report_marker_quality( d['filtered_markers'], 
                                        len(filtered_sample_ids) )

    marker_df = filtered_marker_df
    d['filtered_sample_by_locations'] = group_sample_by_location( filtered_sample_df )

    d['marker_summary'] = generate_allele_summary( marker_df )

    d['location_summary'], strict_sample_ids = generate_location_summary( d['filtered_sample_by_locations'],
                                                        d['filtered_marker_quality'] )

    d['differentiated_samples'] = group_sample_by_differentiation( filtered_sample_ids,
                        differentiation_method = 1 )
    marker_ids = list([ e[1] for e in d['filtered_marker_quality'] if e[-1] ])

    d['differentiated_strict_samples'] = group_sample_by_differentiation( strict_sample_ids,
                        differentiation_method = 1 )
    
    sets = generate_analyticalsets( d['differentiated_samples'], marker_ids )
    strict_sets = generate_analyticalsets( d['differentiated_strict_samples'], marker_ids )

    d['Fst'] = run_arlequin( sets )

    #d['genotypes'] = dominant_genotypes( filtered_sample_ids, threshold,
    #        [ m[1] for m in d['filtered_marker_quality'] if m[4] ] )

    #d['distance'] = pw_distance( d['genotypes'] )
    d['distance'] = pw_distance( sets )
    d['strict_distance'] = pw_distance( strict_sets )

    d['pca'] = pca_distance( d['distance'] )
    d['strict_pca'] = pca_distance( d['strict_distance'] )

    return d


## ------------------------------- NEW ANALYSIS -------------------------------------------- ##

def xxx_generate_analyticalsets( sample_sets, marker_ids=None,
        allele_absolute_threshold = 0, allele_relative_threshold = 0 ):

    units = []
    colours = [ 'red', 'green', 'blue', 'orange', 'purple', 'yellow', 'black', 'magenta',
                    'wheat', 'cyan', 'brown', 'slateblue' ]
    c = 0
    for g in sample_sets:
        units.append( AnalyticalSet( sample_ids = g[1], marker_ids = marker_ids,
                label = g[0], colour = colours[c],
                absolute_threshold = allele_absolute_threshold,
                relative_threshold = allele_relative_threshold
                ) )
        c += 1
    return units


def create_analytical_sets( sample_sets, marker_ids = None, snapshot_id = None,
                allele_absolute_threshold = 0,
                allele_relative_threshold = 0,
                allele_relative_cutoff = 0,
                keep_empty_set = False):

    sets = [ sample_set.get_analyticalset( marker_ids = marker_ids, snapshot_id = snapshot_id,
                    allele_absolute_threshold = allele_absolute_threshold,
                    allele_relative_threshold = allele_relative_threshold,
                    allele_relative_cutoff = allele_relative_cutoff)
                for sample_set in sample_sets ]
    if keep_empty_set:
        return sets
    else:
        return list(filter(None.__ne__, sets))

def get_param( param, default ):
    return param if param is not None else default

def create_analytical_sets2( sample_sets, marker_ids = None, snapshot_id = None,
                allele_absolute_threshold = None,
                allele_relative_threshold = None,
                allele_relative_cutoff = None,
                baseparams = None,
                keep_empty_set = False):

    marker_ids = marker_ids if marker_ids is not None else baseparams.marker_ids
    allele_absolute_threshold = get_param(  allele_absolute_threshold,
                                            baseparams.allele_absolute_threshold )
    allele_relative_threshold = get_param(  allele_relative_threshold,
                                            baseparams.allele_relative_threshold )
    allele_relative_cutoff = get_param( allele_relative_cutoff,
                                        baseparams.allele_relative_cutoff )

    sets = [ sample_set.get_analyticalset( marker_ids = marker_ids, snapshot_id = snapshot_id,
                    allele_absolute_threshold = allele_absolute_threshold,
                    allele_relative_threshold = allele_relative_threshold,
                    allele_relative_cutoff = allele_relative_cutoff,
                    unique = baseparams.unique )
                for sample_set in sample_sets ]

    if keep_empty_set:
        return sets
    else:
        return list(filter(None.__ne__, sets))





def generate_basic_report( sample_df ):

    # create analytical sets for the whole sample sets, this is for allele report
    # analytical_sets = create_analytical_sets( sample_sets )
    R = {}

    # create location report
    R['locations'] = report_by_location( sample_df )

    # create year report
    R['years'] = report_by_year( sample_df )

    # create allele report

    return R


def get_sample_ids( analytical_sets ):

    sample_ids = set()
    for analytical_set in analytical_sets:
        sample_ids.update( analytical_set.get_sample_ids() )
    return sample_ids


def assess_sample_quality( analytical_sets, sample_quality_threshold = 0 ):
    """ return a report on sample quality, with options to filter the sample if
        sample_quality_threshold > 0
        report: [ (label, list_of_failed_genotypes, failed_samples), ... ]
        return: ( report, filtered_sets )
    """

    filtered_sets = []
    reports = []

    # get all marker ids

    marker_ids = set()
    for data_set in analytical_sets:
        marker_ids.update( data_set.get_marker_ids() )

    for data_set in analytical_sets:
        failed_genotypes, failed_samples, filtered_set = data_set.filter_sample_quality(
                        marker_ids = marker_ids,
                        sample_quality_threshold = sample_quality_threshold )

        if len(filtered_set) > 0:
            filtered_sets.append( filtered_set )
        reports.append( (data_set.get_label(), failed_genotypes, failed_samples) )


    return ( reports, filtered_sets)


def assess_marker_quality( analytical_sets, marker_quality_threshold = 0, marker_ids = None ):
    """ return a report on marker quality, with options to filter marker_id if
        marker_quality_threshold > 0
        return: (report, filtered_marker_ids)
    """

    marker_dists = [ data_set.get_marker_distribution() for data_set in analytical_sets ]
    marker_set = functools.reduce( lambda x,y: x.add(y, fill_value=0),
            marker_dists[1:], marker_dists[0] )

    #if marker_ids:
    #    marker_set = marker_set[ marker_set['marker_id'].isin( marker_ids ) ]

    report = []
    passed_marker_ids = []
    N = get_sample_count( analytical_sets )

    for (marker_id, count) in marker_set.iteritems():
        failed_genotypes = N - count
        prop_failed_genotypes = failed_genotypes / count
        if prop_failed_genotypes > marker_quality_threshold:
            status = False
        else:
            status = True
            passed_marker_ids.append( int(marker_id) )
        report.append( (Marker.get(marker_id).code, marker_id, failed_genotypes,
                        prop_failed_genotypes * 100, status) )

    return (report, passed_marker_ids)


def get_sample_count( analytical_sets ):
    """ return total count of samples from the sets """

    return sum( [ data_set.get_N() for data_set in analytical_sets ] )


def filter_strict_samples( analytical_sets ):
    """ return analytical_set list with strict sample,
        strict samples are samples with only 1 locus of multiple alleles
    """

    return [ s.filter_strict_samples() for s in analytical_sets ]


def summarize_markers( analytical_sets, marker_ids = None ):
    """ return unique allele, allele per sample [mean, med, min, max, sd], He, allele frequency
    """

    if marker_ids is None:
        marker_ids = set()
        for s in analytical_sets:
            marker_ids.update( s.get_marker_ids() )

    markers = []
    summaries = []
    for marker_id in marker_ids:
        alleles = []
        dominant_alleles = []
        for s in analytical_sets:
            try:
                alleles.append( s.get_allele_summaries()[marker_id] )
                dominant_alleles.append( s.get_dominant_allele_summaries()[marker_id] )
            except KeyError:
                # marker_id not available in current summary, so just pass
                pass
        summary = combine_allele_summaries( *alleles )
        dominant_summary = combine_allele_summaries( *dominant_alleles )
        markers.append( ( Marker.get(marker_id).code, marker_id,
                            summary.get_unique(), summary.get_moi_stats(),
                            dominant_summary.get_He(), summary.get_polyclonality(),
                            summary.get_distribution(),
                            summary.get_moi_distribution() ) )
        summaries.append( ( Marker.get(marker_id).code, marker_id, summary,
                            dominant_summary.get_He(), summary.get_polyclonality() ) )

    markers.sort( key = itemgetter( 4 ), reverse=True )

    # analyze polyclonality
    # based on He

    summaries.sort( key = itemgetter( 3 ), reverse = True )
    clonality = ClonalitySummary()
    clonality_by_he = []
    for (code, marker_id, summary, he, poly_prop) in summaries:
        clonality.combine( summary.get_samples() )
        clonality_by_he.append( (clonality.polyclonality(), code) )

    summaries.sort( key = itemgetter( 4 ), reverse = True )
    clonality = ClonalitySummary()
    clonality_by_prop = []
    for (code, marker_id, summary, he, poly_prop) in summaries:
        clonality.combine( summary.get_samples() )
        clonality_by_prop.append( (clonality.polyclonality(), code) )


    return dict(    markers=markers,
                    clonality_by_he = clonality_by_he,
                    clonality_by_prop = clonality_by_prop
            )


def summarize_samples( normal_analytical_sets, strict_analytical_sets, marker_ids = None ):
    """ return N, MoI (mean, median, min, max, sd), polyclonality (prop, N), He,
        sample set a) (N, LD, p-val), sample set b) (N, LD, p-val),
        sample set c) (N, LD, p-val)
    """

    report = []

    # add whole country analysis
    country = get_main_country( normal_analytical_sets )
    normal_analytical_sets = normal_analytical_sets + \
                        [ combine_analyticalsets( normal_analytical_sets, country ) ]
    strict_analytical_sets = strict_analytical_sets + \
                        [ combine_analyticalsets( strict_analytical_sets, country ) ]

    for nset, sset in zip( normal_analytical_sets, strict_analytical_sets ):
        report.append( (
            nset.get_label(),
            nset.get_N(),
            nset.get_moi_stats(),
            nset.get_He(),
            run_lian( nset.get_genotypes().dropna() ),
            run_lian( sset.get_genotypes().dropna() ),
            run_lian( nset.get_genotypes().dropna().drop_duplicates() )
        ) )

    return report


def generate_comprehensive_summary_2( sample_ids = None, marker_ids = None,
        location_level = 4, spatial_differentiation = 4, temporal_differentiation = 0,
        allele_absolute_threshold = 100, allele_relative_threshold = 0.33,
        sample_quality_threshold = 0.5, marker_quality_threshold = 0.1,
        querysets = None, tmp_dir = None ):

    if querysets:
        # not implemented yet
        raise NotImplementedError

    # this is for results
    R = {}
    
    if type(sample_ids) == orm.Query:
        N_baseline = sample_ids.count()
    else:
        N_baseline = len(sample_ids)

    # Base Set #1
    # this is for basic reporting, sample & marker quality filtering

    (base_sample_sets, base_sample_df) = group_samples( sample_ids,
                                    spatial_differentiation = location_level )

    # basic reports
    R['sample_size'] = N_baseline
    R['basic'] = generate_basic_report( base_sample_df )

    # sample & marker quality assessment
    base_analytical_sets = create_analytical_sets( base_sample_sets, marker_ids = marker_ids,
                                allele_absolute_threshold = allele_absolute_threshold,
                                allele_relative_threshold = allele_relative_threshold )


    # sample quality assessment
    R['sample_quality'], filtered_analytical_sets = assess_sample_quality( base_analytical_sets,
                sample_quality_threshold = sample_quality_threshold )

    # marker quality assessment
    R['marker_quality'], filtered_marker_ids = assess_marker_quality( filtered_analytical_sets,
                marker_quality_threshold = marker_quality_threshold, marker_ids = marker_ids )


    # Base Set #2
    # we use sample_ids in filtered_analytical_sets

    filtered_sample_ids = get_sample_ids( filtered_analytical_sets )
    R['filtered_sample_size'] = len(filtered_sample_ids)


    (diff_sample_sets, diff_sample_df) = group_samples(
                        filtered_sample_ids,
                        spatial_differentiation = spatial_differentiation,
                        temporal_differentiation = temporal_differentiation )


    main_country = get_main_country( diff_sample_sets )
    country_sample_sets = [ x for x in diff_sample_sets if x.get_country() == main_country ]

    # non haplotyping analysis
    country_analytical_sets = create_analytical_sets( country_sample_sets,
                                marker_ids = marker_ids,
                                allele_absolute_threshold = allele_absolute_threshold,
                                allele_relative_threshold = allele_relative_threshold )

    # haplotyping analysis
    diff_analytical_sets = create_analytical_sets( diff_sample_sets,
                                marker_ids = filtered_marker_ids,
                                allele_absolute_threshold = allele_absolute_threshold,
                                allele_relative_threshold = allele_relative_threshold )


    strict_analytical_sets = filter_strict_samples( diff_analytical_sets )

    # create summarized reports for markers & samples
    R['marker_summary'] = summarize_markers( country_analytical_sets )
    R['diff_summary'] = summarize_samples( diff_analytical_sets, strict_analytical_sets )

    R['Fst'] = run_arlequin( diff_analytical_sets, tmp_dir = tmp_dir + '-arlequin' )
    R['Fst_max'] = run_arlequin( diff_analytical_sets, recode = True,
                            tmp_dir = tmp_dir + '-arlequin-recode' )

    R['Fst_std'] = standardized_fst( R['Fst'], R['Fst_max'] )

    R['base_distance'] = pw_distance( diff_analytical_sets )
    R['strict_distance'] = pw_distance( strict_analytical_sets )

    R['base_pca'] = pca_distance( R['base_distance'] )
    R['strict_pca'] = pca_distance( R['strict_distance'] )

    return R


def get_filtered_analytical_sets( sample_ids, marker_ids,
                allele_absolute_threshold, allele_relative_threshold,
                sample_quality_threshold, marker_quality_threshold,
                spatial_differentiation, temporal_differentiation,
                allele_relative_cutoff = 0):

    """ return (analytical_sets, sample_report, marker_report)
    """

    sample_sets, sample_df = group_samples( sample_ids,
                                        spatial_differentiation = spatial_differentiation,
                                        temporal_differentiation = temporal_differentiation )

    base_analytical_sets = create_analytical_sets( sample_sets, marker_ids = marker_ids,
                            allele_absolute_threshold = allele_absolute_threshold,
                            allele_relative_threshold = allele_relative_threshold,
                            allele_relative_cutoff = allele_relative_cutoff)

    sample_report, filtered_analytical_sets = assess_sample_quality( base_analytical_sets,
                            sample_quality_threshold = sample_quality_threshold )

    marker_report, filtered_marker_ids = assess_marker_quality( filtered_analytical_sets,
                            marker_quality_threshold = marker_quality_threshold )

    diff_sample_sets, diff_sample_df = group_samples( get_sample_ids(filtered_analytical_sets),
                            spatial_differentiation = spatial_differentiation,
                            temporal_differentiation = temporal_differentiation )

    diff_analytical_sets = create_analytical_sets( diff_sample_sets,
                            marker_ids = filtered_marker_ids,
                            allele_absolute_threshold = allele_absolute_threshold,
                            allele_relative_threshold = allele_relative_threshold,
                            allele_relative_cutoff = allele_relative_cutoff)

    return (diff_analytical_sets, sample_report, marker_report)


def get_filtered_analytical_sets2( sample_sets, baseparams,
                                    spatial_differentiation = 0,
                                    temporal_differentiation = 0,
                                    detection_differentiation = False):

    # create base_sample_sets & sample_df, based of sample_sets and further differetiated
    # by spatial / temporal setting
    base_sample_sets, sample_df = group_samples2( sample_sets,
                                    spatial_differentiation = spatial_differentiation,
                                    temporal_differentiation = temporal_differentiation,
                                    detection_differentiation = detection_differentiation)

    base_analytical_sets = create_analytical_sets2( base_sample_sets, baseparams = baseparams )

    sample_report, filtered_analytical_sets = assess_sample_quality( base_analytical_sets,
                            sample_quality_threshold = baseparams.sample_quality_threshold )

    marker_report, filtered_marker_ids = assess_marker_quality( filtered_analytical_sets,
                            marker_quality_threshold = baseparams.marker_quality_threshold )

    #diff_sample_sets, diff_sample_df = group_samples2(
    #                        filter_sample_sets( base_sample_sets,
    #                                            get_sample_ids(filtered_analytical_sets) ),
    #                        spatial_differentiation = spatial_differentiation,
    #                        temporal_differentiation = temporal_differentiation )
    diff_sample_sets = filter_sample_sets( base_sample_sets,
                                            get_sample_ids(filtered_analytical_sets) )

    diff_analytical_sets = create_analytical_sets2( diff_sample_sets,
                            marker_ids = filtered_marker_ids,
                            baseparams = baseparams )

    return (diff_analytical_sets, sample_report, marker_report)


def filter_sample_sets( sample_sets, sample_ids ):
    """ return a new sample_sets, but only with sample_ids
    """
    
    return [ ss.filter_sampleids( sample_ids) for ss in sample_sets ]


def generate_comprehensive_summary_3( sample_sets, baseparams,
        location_level = 4, spatial_differentiation = 4, temporal_differentiation = 0,
        detection_differentiation = False,
        tmp_dir = None ):

    # this is for results
    R = {}
    
    N_baseline = sum( len(sample_set) for sample_set in sample_sets )

    # Base Set #1
    # this is for basic reporting, sample & marker quality filtering

    (base_sample_sets, base_sample_df) = group_samples2( sample_sets,
                                    spatial_differentiation = location_level,
                                    detection_differentiation = detection_differentiation)

    # basic reports
    R['sample_size'] = N_baseline
    R['basic'] = generate_basic_report( base_sample_df )

    # sample & marker quality assessment
    #base_analytical_sets = create_analytical_sets( base_sample_sets, marker_ids = marker_ids,
    #                            allele_absolute_threshold = allele_absolute_threshold,
    #                            allele_relative_threshold = allele_relative_threshold )
    base_analytical_sets = create_analytical_sets2( base_sample_sets,
                                                    baseparams = baseparams )



    # sample quality assessment
    R['sample_quality'], filtered_analytical_sets = assess_sample_quality( base_analytical_sets,
                sample_quality_threshold = baseparams.sample_quality_threshold )

    # marker quality assessment
    R['marker_quality'], filtered_marker_ids = assess_marker_quality( filtered_analytical_sets,
                marker_quality_threshold = baseparams.marker_quality_threshold )


    # Base Set #2
    # we use sample_ids in filtered_analytical_sets

    filtered_sample_ids = get_sample_ids( filtered_analytical_sets )
    R['filtered_sample_size'] = len(filtered_sample_ids)


    (diff_sample_sets, diff_sample_df) = group_samples2(
                        filter_sample_sets( sample_sets, filtered_sample_ids ),
                        spatial_differentiation = spatial_differentiation,
                        temporal_differentiation = temporal_differentiation,
                        detection_differentiation = detection_differentiation)

    main_country = get_main_country( diff_sample_sets )
    country_sample_sets = [ x for x in diff_sample_sets if x.get_country() == main_country ]

    # non haplotyping analysis
    country_analytical_sets = create_analytical_sets2( country_sample_sets,
                                baseparams = baseparams )

    # haplotyping analysis
    diff_analytical_sets = create_analytical_sets2( diff_sample_sets,
                                marker_ids = filtered_marker_ids,
                                baseparams = baseparams )


    strict_analytical_sets = filter_strict_samples( diff_analytical_sets )

    # create summarized reports for markers & samples
    R['marker_summary'] = summarize_markers( country_analytical_sets )
    R['diff_summary'] = summarize_samples( diff_analytical_sets, strict_analytical_sets )

    R['Fst'] = run_arlequin( diff_analytical_sets, tmp_dir = tmp_dir + 'arlequin' )
    R['Fst_max'] = run_arlequin( diff_analytical_sets, recode = True,
                            tmp_dir = tmp_dir + 'arlequin-recode' )

    R['Fst_std'] = standardized_fst( R['Fst'], R['Fst_max'] )

    R['base_distance'] = pw_distance( diff_analytical_sets )
    R['strict_distance'] = pw_distance( strict_analytical_sets )

    R['base_pca'] = pca_distance( R['base_distance'] )
    R['strict_pca'] = pca_distance( R['strict_distance'] )

    return R

