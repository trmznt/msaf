
# mandatory imports

import logging

log = logging.getLogger(__name__)

from pyramid.response import FileResponse
from pyramid.renderers import render_to_response
from pyramid.httpexceptions import HTTPFound

from rhombus.lib.roles import PUBLIC
from rhombus.views import roles
from rhombus.views.errors import error_page
from rhombus.lib import fsoverlay as fso

from msaf.lib.querycmd import parse_querycmd, get_queries
from msaf.lib.advquerycmd import parse_advquerycmd
from msaf.lib.analytics import group_samples, get_sample_ids
#from msaf.lib.tools.summary import ( create_analytical_sets, assess_sample_quality,
#        assess_marker_quality )
from msaf.lib.tools.summary import get_filtered_analytical_sets, get_filtered_analytical_sets2

from msaf.views.utils import get_marker_list, parse_base_params
from msaf.models import Marker, Sample

from pandas import pivot_table
from itertools import zip_longest
import numpy as np
import csv, io


@roles( PUBLIC )
def index(request):

    if not request.GET.get('_method', None) == '_exec':
        queries = get_queries()

        return render_to_response('msaf:templates/tools/genotype/index.mako',
                { 'queries': queries, 'markers': get_marker_list() },
                request = request)


    #parse form

    baseparams = parse_base_params( request.GET )
    spatial_differentiation = int(request.GET.get('spatial_differentiation', -1))
    temporal_differentiation = int(request.GET.get('temporal_differentiation', 0))


    # filter samples

    #sample_ids = parse_querycmd( baseparams.queryset )
    sample_sets = parse_advquerycmd( baseparams.queryset )
    diff_analytical_sets, sample_report, marker_report = get_filtered_analytical_sets2(
                sample_sets = sample_sets,
                baseparams = baseparams,
                spatial_differentiation = spatial_differentiation,
                temporal_differentiation = temporal_differentiation )
    #raise RuntimeError
    #diff_analytical_sets, sample_report, marker_report = get_filtered_analytical_sets2(
    #            sample_ids = sample_ids, marker_ids = baseparams.marker_ids,
    #            allele_absolute_threshold = baseparams.allele_absolute_threshold,
    #            allele_relative_threshold = baseparams.allele_relative_threshold,
    #            allele_relative_cutoff = baseparams.allele_relative_cutoff,
    #            sample_quality_threshold = baseparams.sample_quality_threshold,
    #            marker_quality_threshold = baseparams.marker_quality_threshold,
    #            spatial_differentiation = spatial_differentiation,
    #            temporal_differentiation = temporal_differentiation )


    #sample_sets, sample_df = group_samples( sample_ids,
    #                                    spatial_differentiation = spatial_differentiation,
    #                                    temporal_differentiation = temporal_differentiation )

    #base_analytical_sets = create_analytical_sets( sample_sets,
    #                        marker_ids = baseparams.marker_ids,
    #                        allele_absolute_threshold = baseparams.allele_absolute_threshold,
    #                        allele_relative_threshold = baseparams.allele_relative_threshold,
    #                        allele_relative_cutoff = baseparams.allele_relative_cutoff)

    #sample_report, filtered_analytical_sets = assess_sample_quality( base_analytical_sets,
    #                        sample_quality_threshold = baseparams.sample_quality_threshold )

    #marker_report, filtered_marker_ids = assess_marker_quality( filtered_analytical_sets,
    #                        marker_quality_threshold = baseparams.marker_quality_threshold )

    #diff_sample_sets, diff_sample_df = group_samples( get_sample_ids(filtered_analytical_sets),
    #                        spatial_differentiation = spatial_differentiation,
    #                        temporal_differentiation = temporal_differentiation )

    #diff_analytical_sets = create_analytical_sets( diff_sample_sets,
    #                        marker_ids = filtered_marker_ids,
    #                        allele_absolute_threshold = baseparams.allele_absolute_threshold,
    #                        allele_relative_threshold = baseparams.allele_relative_threshold )

    # start analysis here

    #genotype_summary = summarize_genotypes( diff_analytical_sets )

    reports = []

    for analytical_set in diff_analytical_sets:

        data, aux_data, assay_data = prepare_data( analytical_set.get_allele_df() )
        reports.append( ( analytical_set.get_label(), data, aux_data, assay_data ))

    temp_dir = fso.mkranddir( '/temps' )
    tabfile = temp_dir.rpath + '/genotypes.tab'
    with open(tabfile, 'w') as f:
        writer = csv.writer(f, delimiter='\t')
        for (label, rows, aux_rows, assay_rows) in reports:
            writer.writerow(('Label: %s' % label,))
            writer.writerows( rows )
    
    return render_to_response('msaf:templates/tools/genotype/report.mako',
            { 'reports': reports, 'tabfile': fso.get_urlpath(tabfile) },
            request = request )


def prepare_data( allele_df ):

    #buf = io.StringIO()

    #temp_csv = csv.writer( buf, delimiter='\t' )
    buf = []
    buf2 = []
    buf3 = []

    table = pivot_table( allele_df, rows='sample_id', cols='marker_id', values='value',
                            aggfunc = lambda x: tuple(x) )

    heights = pivot_table( allele_df, rows='sample_id', cols='marker_id', values='height',
                            aggfunc = lambda x: tuple(x) )

    assay_ids = pivot_table( allele_df, rows='sample_id', cols='marker_id', values='assay_id',
                            aggfunc = lambda x: tuple(x) )

    buf.append( tuple( ['Sample'] + 
                    [ Marker.get(x).code for x in table.columns ] ) )
    buf2.append( tuple( ['Sample'] + 
                    [ Marker.get(x).code for x in heights.columns ] ) )
    buf3.append( tuple( ['Sample'] +
                    [ Marker.get(x).code for x in assay_ids.columns ] ) )


    empty = tuple()

    rows = [ (((Sample.get(r[0]).code, r[0]),),) + r[1:] for r in table.itertuples() ]
    rows.sort()

    height_rows = [ (((Sample.get(r[0]).code, r[0]),),) + r[1:]
                                for r in heights.itertuples() ]
    height_rows.sort()

    assayid_rows = [ (((Sample.get(r[0]).code, r[0]),),) + r[1:]
                                for r in assay_ids.itertuples() ]
    assayid_rows.sort()

    for row in rows:
        data = [ x if type(x) == tuple else empty for x in row ]
        for cols in zip_longest( *data, fillvalue='' ):
            buf.append( cols )

    for height_row in height_rows:
        data = [ x if type(x) == tuple else empty for x in height_row ]
        for cols in zip_longest( *data, fillvalue='' ):
            buf2.append( cols )

    for assayid_row in assayid_rows:
        data = [ x if type(x) == tuple else empty for x in assayid_row ]
        for cols in zip_longest( *data, fillvalue='' ):
            buf3.append( cols )


    return (buf, buf2, buf3)





    
