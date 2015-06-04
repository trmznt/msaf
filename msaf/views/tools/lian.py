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
from msaf.views.utils import get_marker_list

# spesific imports
from msaf.lib.tools.lian import lian



@roles( PUBLIC )
def index(request):

    if not request.GET.get('_method', None) == '_exec':
        # show form page
        queries = get_queries()

        return render_to_response('msaf:templates/tools/lian/index.mako',
                { 'queries': queries, 'markers': get_marker_list() },
                request = request)

    # parse form
    queryset = request.GET.get('queryset', '').strip()
    threshold = request.GET.get('threshold', 0)
    markers = request.GET.getall('markers')

    result = lian(queryset, threshold, markers)

    return render_to_response('msaf:templates/tools/lian/report.mako',
            { 'result': result },
            request = request)

