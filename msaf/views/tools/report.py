
# mandatory imports

import logging

log = logging.getLogger(__name__)

from pyramid.response import FileResponse
from pyramid.renderers import render_to_response
from pyramid.httpexceptions import HTTPFound

from rhombus.lib.roles import PUBLIC
from rhombus.views import roles
from rhombus.views.errors import error_page

from msaf.lib.querycmd import parse_querycmd, get_queries
from msaf.lib.advquerycmd import parse_advquerycmd
from msaf.views.utils import get_marker_list
from msaf.views.utils import get_marker_list, parse_base_params


# spesific imports
from msaf.lib.queryfuncs import MarkerDF, generate_allele_summary
from msaf.lib.tools.report import generate_report_2, generate_report_3


@roles( PUBLIC )
def index(request):

    if not request.GET.get('_method', None) == '_exec':
        # show form page
        queries = get_queries()

        return render_to_response('msaf:templates/tools/report/index.mako',
                { 'queries': queries, 'markers': get_marker_list() },
                request = request)

    # parse form
    #queryset = request.GET.get('queryset', '').strip()
    #batchcode = request.GET.get('batchcode', '')
    #marker_ids = [ int(x) for x in request.GET.getall('markers') ]
    #allele_absolute_threshold = int(request.GET.get('allele_absolute_threshold', 100))
    #allele_relative_threshold = float(request.GET.get('allele_relative_threshold', 0.33))
    #sample_quality_threshold = float(request.GET.get('sample_quality_threshold', 0.50))
    #marker_quality_threshold = float(request.GET.get('marker_quality_threshold', 0.10))
    #location_level = int(request.GET.get('location_level', 4))
    #spatial_differentiation = int(request.GET.get('spatial_differentiation', 4))
    #temporal_differentiation = int(request.GET.get('temporal_differentiation', 0))

    baseparams = parse_base_params( request.GET )
    location_level = int(request.GET.get('location_level', 4))
    spatial_differentiation = int(request.GET.get('spatial_differentiation', -1))
    temporal_differentiation = int(request.GET.get('temporal_differentiation', 0))
    detection_differentiation = int(request.GET.get('detection_differentiation', 0))

    #report = generate_report( batchcode, queryset, location_level, threshold,
    #        template_file = request.get_resource('custom.report', '') )

    if False:
        report = generate_report_2( batchcode, queryset, marker_ids,
                allele_absolute_threshold, allele_relative_threshold,
                sample_quality_threshold, marker_quality_threshold,
                location_level, spatial_differentiation, temporal_differentiation,
                template_file = request.get_resource('custom.report', '') )

    
    report = generate_report_3( baseparams,
                        location_level = location_level,
                        spatial_differentiation = spatial_differentiation,
                        temporal_differentiation = temporal_differentiation,
                        detection_differentiation = detection_differentiation,
                        template_file = request.get_resource('custom.report', '') )


    response = FileResponse(report.fullpath)
    response.headers['Content-Disposition'] = ("attachment; filename=report.pdf")
    return response

    
# need to return
# "Content-Disposiiton: inline; filename=abcdef.pdf"
# response = FileResponse('/some/path/to/a/file.txt')
# response.headers['Content-Disposition'] = ("attachment; filename=Export.xml")
# return response




        
    


