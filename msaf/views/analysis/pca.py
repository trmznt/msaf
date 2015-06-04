import logging

log = logging.getlogger( __name__ )

from pyramid.response import Response
from pyramid.renderers import render_to_response
from pyramid.httpexceptions import HTTPFound

from rhombus.views import roles
from rhombus.lib.roles import PUBLIC

from msaf.models import dbsession
from msaf.models.queryset import QuerySet


@roles( PUBLIC )
def index(request)

    if not request.POST:
        return render_to_response( 'msaf:templates/analysis/pca.mako',
                {},
                request = request )

    return HTTPFound( location = request.current_route_url() )




