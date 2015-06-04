
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
from msaf.lib.tools.summary import get_filtered_analytical_sets2
from msaf.lib.tools.summary import get_filtered_analytical_sets
from msaf.views.utils import get_marker_list, parse_base_params, parse_yaml_params, set_base_params

# analysis spesific imports

from msaf.lib.tools.allele import summarize_alleles2

@roles( PUBLIC )
def index(request):

    if not request.GET.get('_method', None) in ['_exec', '_yamlexec']:
        queries = get_queries()

        return render_to_response('msaf:templates/tools/allele/index.mako',
                { 'queries': queries, 'markers': get_marker_list() },
                request = request)

    if request.GET.get('_method') == '_exec':

    #parse form

        baseparams = parse_base_params( request.GET )
        spatial_differentiation = int(request.GET.get('spatial_differentiation', -1))
        temporal_differentiation = int(request.GET.get('temporal_differentiation', 0))
        sample_sets = parse_advquerycmd( baseparams.queryset )



    else:
        selector, filter, differentiation = parse_yaml_params( request.GET )
        baseparams = set_base_params(selector, filter)
        spatial_differentiation = differentiation.spatial
        temporal_differentiation = differentiation.temporal
        sample_sets = selector.get_sample_sets()


    #sample_ids = parse_querycmd( baseparams.queryset )
    #diff_analytical_sets, sample_report, marker_report = get_filtered_analytical_sets(
    #            sample_ids = sample_ids, marker_ids = baseparams.marker_ids,
    #            allele_absolute_threshold = baseparams.allele_absolute_threshold,
    #            allele_relative_threshold = baseparams.allele_relative_threshold,
    #            sample_quality_threshold = baseparams.sample_quality_threshold,
    #            marker_quality_threshold = baseparams.marker_quality_threshold,
    #            spatial_differentiation = spatial_differentiation,
    #            temporal_differentiation = temporal_differentiation)

    #analytical_set = diff_analytical_sets[0]

    diff_analytical_sets, sample_report, marker_report = get_filtered_analytical_sets2(
                sample_sets = sample_sets,
                baseparams = baseparams,
                spatial_differentiation = spatial_differentiation,
                temporal_differentiation = temporal_differentiation )


    # need to get all alleles from all peaks, including size & height

    temp_dir = fso.mkranddir( '/temps' )

    results, plot_file = summarize_alleles2( diff_analytical_sets, temp_dir.rpath )
    ploturl = fso.get_urlpath( plot_file )

    return render_to_response('msaf:templates/tools/allele/report.mako',
            {   'results': results,
                'ploturl': ploturl
            },
            request = request )

