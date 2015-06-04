
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
from msaf.views.utils import get_marker_list, parse_base_params

from msaf.lib.tools.he import summarize_he, df_to_rows


@roles( PUBLIC )
def index(request):

    if not request.GET.get('_method', None) == '_exec':
        queries = get_queries()

        return render_to_response('msaf:templates/tools/he/index.mako',
                { 'queries': queries, 'markers': get_marker_list() },
                request = request)


    #parse form

    baseparams = parse_base_params( request.GET )
    spatial_differentiation = int(request.GET.get('spatial_differentiation', -1))
    temporal_differentiation = int(request.GET.get('temporal_differentiation', 0))
    detection_differentiation = int(request.GET.get('detection_differentiation', 0))

    sample_sets = parse_advquerycmd( baseparams.queryset )
    diff_analytical_sets, sample_report, marker_report = get_filtered_analytical_sets2(
                sample_sets = sample_sets,
                baseparams = baseparams,
                spatial_differentiation = spatial_differentiation,
                temporal_differentiation = temporal_differentiation,
                detection_differentiation = detection_differentiation)
    
    reports = summarize_he( diff_analytical_sets )

    table = reports['table']

    # need to get all alleles from all peaks, including size & height

    #temp_dir = fso.mkranddir( '/temps' )

    #results, plot_file = summarize_alleles( analytical_set.get_allele_df(), temp_dir.rpath )
    #ploturl = fso.get_urlpath( plot_file )

    return render_to_response('msaf:templates/tools/he/report.mako',
            {   'reports': reports,
                'table': table,
            },
            request = request )

