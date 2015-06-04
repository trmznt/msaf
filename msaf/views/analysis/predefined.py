import logging

from pyramid.response import Response
from pyramid.renderers import render_to_response
from pyramid.httpexceptions import HTTPFound

log = logging.getLogger(__name__)

def index(request):
    return render_to_response( "msaf:templates/analysis/predefined.mako",
        {}, request=request )
