# mandatory imports

import logging

log = logging.getLogger(__name__)

from pyramid.response import FileResponse, FileIter
from pyramid.renderers import render_to_response
from pyramid.httpexceptions import HTTPFound

from rhombus.lib.roles import PUBLIC
from rhombus.views import roles
from rhombus.views.errors import error_page

from msaf.lib.querycmd import parse_querycmd, get_queries

from msaf.lib.tools.export import export_data
from msaf.views.utils import get_marker_list



@roles( PUBLIC )
def index(request):

    if not request.GET.get('_method', None) == '_exec':
        # show form page
        queries = get_queries()
        markers = get_marker_list()

        return render_to_response('msaf:templates/tools/export/index.mako',
                { 'queries': queries, 'markers': markers },
                request = request)

    # parse form
    queryset = request.GET.get('queryset', '').strip()
    threshold = request.GET.get('threshold', 0)
    markers = request.GET.getall('markers')

    fmt = request.GET.get('fmt', 'flat')
    filename = request.GET.get('filename', 'vvx-data-export.txt')

    fp = export_data( queryset, threshold, markers, fmt )

    response = request.response
    response.content_type = 'text/plain'
    response.app_iter = FileIter(fp)
    return response

    response = FileResponse(report.fullpath)
    response.headers['Content-Disposition'] = ("attachment; filename=%s" % filename)
    return response

