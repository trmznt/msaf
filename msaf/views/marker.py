import logging

log = logging.getLogger(__name__)

from pyramid.response import Response
from pyramid.renderers import render_to_response
from pyramid.httpexceptions import HTTPFound


from msaf.models import dbsession
from msaf.models.msdb import Marker, Sample

from rhombus.lib.roles import PUBLIC, SYSADM, SYSVIEW
from rhombus.views import roles
from rhombus.views.errors import error_page
from rhombus.lib.paginate import SqlalchemyOrmPage as Page

from msaf.lib.analysis.summary import summarise_allele

import json




@roles( PUBLIC )
def index(request):

    q = Marker.query().order_by( Marker.code )

    markers = Page( q,
                page = int(request.params.get('page', 1)),
                items_per_page=20 )
                #url=page_url )

    return render_to_response( "msaf:templates/marker/index.mako",
                                { 'markers': markers },
                                request=request )


@roles( PUBLIC )
def view(request):

    marker_id = int(request.matchdict.get('id'))
    marker = Marker.get(marker_id)

    return render_to_response( "msaf:templates/marker/view.mako",
            { 'marker': marker }, request = request )



    #threshold = int(request.GET.get('threshold', 0))
    #ms = MarkerSet.get( markerset_id )
    #q = dbsession.query( Sample.id )
    #res = summarise_allele( q, markerset_id, threshold )
    #return render_to_response( "msaf:templates/marker/view.mako",
    #    { 'summary': res, 'ms': ms }, request=request )


@roles( SYSADM )
def edit(request):

    marker_id = int(request.matchdict.get('id'))
    if marker_id < 0:
        return error_page()

    if marker_id == 0:
        marker = Marker( id=0, species='X' )

    else:
        marker = Marker.get(marker_id)
        if not marker:
            return error_page()

    return render_to_response( "msaf:templates/marker/edit.mako",
            { 'marker': marker }, request=request )


@roles( SYSADM )
def save(request):

    if not request.POST:
        return error_page("not a POST command")

    marker_id = int(request.matchdict.get('id'))
    marker = parse_form(request.POST)

    if marker_id != marker.id:
        return error_page()

    if marker.id == 0:
        if not request.has_roles( SYSADM ):
            return not_authorized()

        marker.id = None
        dbsession.add( marker )
        dbsession.flush()
        db_marker = marker
        request.session.flash( ('success', 'Marker [%s] has beed added' % db_marker.code) )

    else:

        if not request.has_roles( SYSADM ):
            return not_authorized()

        db_marker = Marker.get( marker_id )
        db_marker.update( marker )
        request.session.flash( ('success', 'Marker [%s] has been updated' % db_marker.code) )

    return HTTPFound(location = request.route_url('msaf.marker-view', id=db_marker.id))


def parse_form( d ):

    m = Marker()
    m.id = int(d.get('msaf/marker.id', 0))
    m.code = d.get('msaf/marker.code')
    m.locus = d.get('msaf/marker.locus')
    m.species = d.get('msaf/marker.species')
    m.repeats = int(d.get('msaf/marker.repeats') or 0)
    m.min_size = int(d.get('msaf/marker.min_size') or 0)
    m.max_size = int(d.get('msaf/marker.max_size') or 0)
    m.bins = json.loads(d.get('msaf/marker.bins') or '[]')

    return m

def action(request):
    pass

