import logging

log = logging.getLogger(__name__)

from pyramid.response import Response
from pyramid.renderers import render_to_response
from pyramid.httpexceptions import HTTPFound
from msaf.models import dbsession
from msaf.models.msdb import Sample
from msaf.models.queryset import QuerySet, queried_samples
from rhombus.lib.roles import PUBLIC
from rhombus.views import roles

#from webhelpers import paginate
from msaf.lib.querycmd import parse_querycmd, insert_queryset, docs
import transaction

@roles( PUBLIC )
def index(request):

    if not request.POST:
        queries = QuerySet.query().filter( QuerySet.lastuser_id == request.userid() ).order_by(
                    QuerySet.id.desc() )
        return render_to_response( "msaf:templates/queryset/index.mako",
                { 'ticket': '', 'queries': queries, 'docs': docs},
                request=request )

    if request.POST.get('_method', None) == '_querytext':
        do_querytext( request )

    elif request.POST.get('_method', None) == '_queryform':
        do_queryform( request )

    elif request.POST.get('_method', None) == '_querytest':
        c = do_querytext( request, True )
        return render_to_response("msaf:templates/queryset/test.mako",
                { 'text': 'Result: %d samples' % c },
                request = request )

    return HTTPFound( location = request.current_route_url() )


def do_querytext(request, test=False):

    querytext = request.POST.get('query_text', '')
    description = request.POST.get('desc', '')

    if not querytext:
        request.session.flash( ('error', 'You need to fill the query text') )
        return

    q = parse_querycmd( querytext )

    with transaction.manager:

        c = q.count()
        if c > 0 and not test:
            qs = QuerySet( desc=description or None, count = c, query_text = querytext )
            dbsession.add(qs)
            dbsession.flush()

            expr = insert_queryset( q, qs.id )
            dbsession.execute(expr)

    if not test:
        request.session.flash( ('info', 'Your query results in %d samples' % c) )

    return c



