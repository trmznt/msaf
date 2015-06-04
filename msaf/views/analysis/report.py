import logging

log = logging.getLogger(__name__)

from pyramid.response import Response
from pyramid.renderers import render_to_response
from pyramid.httpexceptions import HTTPFound


from msaf.lib.querycmd import parse_querycmd

from rhombus.lib.roles import PUBLIC
from rhombus.views import roles
from rhombus.views.errors import error_page, not_authorized

from msaf.views.utils import get_marker_list


@roles( PUBLIC )
def index(request):
    
    if not request.GET.get('_method', None) == '_exec':
        
        markers = get_marker_list()
        queries = get_queries()

        return render_to_response('msaf:templates/analysis/report/index.mako',
            { 'markers': markers, 'queries': queries },
            request = request )


    queryset = request.GET.get( 'queryset', '' )
    markers = request.GET.getall('markers')
    threshold = request.GET.get('threshold', None)

    report = generate_report( queryset, markers, threshold )

    return render_to_response('msaf:templates/analysis/allele/report/output.mako'


