
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

from msaf.lib.tools.export import export_structure


@roles( PUBLIC )
def index(request):

    if not request.GET.get('_method', None) == '_exec':
        queries = get_queries()

        return render_to_response('msaf:templates/tools/structure/index.mako',
                { 'queries': queries, 'markers': get_marker_list() },
                request = request)


    #parse form

    baseparams = parse_base_params( request.GET )
    spatial_differentiation = int(request.GET.get('spatial_differentiation', 4))
    temporal_differentiation = int(request.GET.get('temporal_differentiation', 0))


    # filter samples

    sample_ids = parse_querycmd( baseparams.queryset )
    sample_sets, sample_df = group_samples( sample_ids,
                                        spatial_differentiation = spatial_differentiation,
                                        temporal_differentiation = temporal_differentiation )

    base_analytical_sets = create_analytical_sets( sample_sets,
                            marker_ids = baseparams.marker_ids,
                            allele_absolute_threshold = baseparams.allele_absolute_threshold,
                            allele_relative_threshold = baseparams.allele_relative_threshold )

    sample_report, filtered_analytical_sets = assess_sample_quality( base_analytical_sets,
                            sample_quality_threshold = baseparams.sample_quality_threshold )

    marker_report, filtered_marker_ids = assess_marker_quality( filtered_analytical_sets,
                            marker_quality_threshold = baseparams.marker_quality_threshold )

    diff_sample_sets, diff_sample_df = group_samples( get_sample_ids(filtered_analytical_sets),
                            spatial_differentiation = spatial_differentiation,
                            temporal_differentiation = temporal_differentiation )

    diff_analytical_sets = create_analytical_sets( diff_sample_sets,
                            marker_ids = filtered_marker_ids,
                            allele_absolute_threshold = baseparams.allele_absolute_threshold,
                            allele_relative_threshold = baseparams.allele_relative_threshold )


    # start analysis here

    (databuf, parambuf) = export_structure( diff_analytical_sets )

    temp_dir = fso.mkranddir( '/temps' )
    infile = temp_dir.rpath + '/infile.txt'
    paramfile = temp_dir.rpath + '/baseparams.txt'
    with open( infile, 'w' ) as f:
        f.write( databuf )
    with open( paramfile, 'w') as f:
        f.write( parambuf )
    #pca_file = plot_pca( base_pca, base_pwdist, temp_dir.rpath, "base-pca.png" )
    #vpath_basepca = fso.get_urlpath( pca_file )


    return render_to_response('msaf:templates/tools/structure/report.mako',
            { 'infile': fso.get_urlpath( infile ), 'paramfile': fso.get_urlpath( paramfile ) },
            request = request )

