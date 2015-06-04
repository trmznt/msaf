
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
from msaf.lib.analytics import group_samples, get_sample_ids
from msaf.lib.tools.summary import ( create_analytical_sets, assess_sample_quality,
        assess_marker_quality )
from msaf.views.utils import get_marker_list, parse_base_params
from msaf.lib.advquerycmd import parse_advquerycmd
from msaf.lib.tools.summary import get_filtered_analytical_sets2


from msaf.lib.tools.distance import pw_distance, pca_distance2, plot_pca2
from itertools import combinations


@roles( PUBLIC )
def index(request):

    if not request.GET.get('_method', None) == '_exec':
        queries = get_queries()

        return render_to_response('msaf:templates/tools/pca/index.mako',
                { 'queries': queries, 'markers': get_marker_list() },
                request = request)


    #parse form

    #baseparams = parse_base_params( request.GET )
    #spatial_differentiation = int(request.GET.get('spatial_differentiation', 4))
    #temporal_differentiation = int(request.GET.get('temporal_differentiation', 0))
    dimension = int(request.GET.get('dimension', 2))

    baseparams = parse_base_params( request.GET )
    spatial_differentiation = int(request.GET.get('spatial_differentiation', -1))
    temporal_differentiation = int(request.GET.get('temporal_differentiation', 0))

    sample_sets = parse_advquerycmd( baseparams.queryset )
    diff_analytical_sets, sample_report, marker_report = get_filtered_analytical_sets2(
                sample_sets = sample_sets,
                baseparams = baseparams,
                spatial_differentiation = spatial_differentiation,
                temporal_differentiation = temporal_differentiation )


    #sample_ids = parse_querycmd( baseparams.queryset )
    #sample_sets, sample_df = group_samples( sample_ids,
    #                                    spatial_differentiation = spatial_differentiation,
    #                                    temporal_differentiation = temporal_differentiation )

    #base_analytical_sets = create_analytical_sets( sample_sets,
    #                        marker_ids = baseparams.marker_ids,
    #                        allele_absolute_threshold = baseparams.allele_absolute_threshold,
    #                        allele_relative_threshold = baseparams.allele_relative_threshold )

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


    base_pwdist = pw_distance( diff_analytical_sets )
    base_pca = pca_distance2( base_pwdist, dimension )


    temp_dir = fso.mkranddir( '/temps' )

    vpaths_basepca = []
    for (ax, ay) in combinations( range( dimension ), 2 ):

        filename = 'base-pca-%d-%d' % (ax, ay)
        pca_file = plot_pca2( base_pca, base_pwdist, ax, ay, temp_dir.rpath, filename + '.png' )
        pca_pdf = plot_pca2( base_pca, base_pwdist, ax, ay, temp_dir.rpath, filename + '.pdf' )
        vpaths_basepca.append( fso.get_urlpath( pca_file ) )

    return render_to_response('msaf:templates/tools/pca/report.mako',
            { 'vpaths_basepca': vpaths_basepca },
            request = request )



