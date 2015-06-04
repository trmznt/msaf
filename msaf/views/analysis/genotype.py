import logging

log = logging.getLogger(__name__)

from pyramid.response import Response
from pyramid.renderers import render_to_response
from pyramid.httpexceptions import HTTPFound
from msaf.models import dbsession
from msaf.models.msdb import Sample, Marker
from msaf.models.queryset import QuerySet, queried_samples
from msaf.lib.querycmd import get_queries, parse_querycmd
from rhombus.lib.roles import PUBLIC
from rhombus.views import roles

#from webhelpers import paginate

from msaf.lib.querycmd import parse_querycmd, insert_queryset, docs
import transaction

from msaf.lib.analysis.summary import dominant_genotype

@roles( PUBLIC )
def index(request):

    if not request.GET.get('_method', None) == '_exec':

        # this can be put into function
        markersets = Marker.query().order_by( Marker.name )
        queries = get_queries()

        return render_to_response('msaf:templates/analysis/genotype/index.mako',
            { 'markersets': markersets, 'queries': queries },
            request = request )

    queryset = request.GET.getall('queryset')
    markers = request.GET.getall('markers')
    threshold = int(request.GET.get('threshold', 0) or 0)

    for q in queryset:

        sample_ids = parse_querycmd( q )

        genotype = dominant_genotype( sample_ids, markers, threshold )

        raise RuntimeError
