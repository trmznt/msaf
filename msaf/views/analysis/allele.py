import logging

log = logging.getLogger(__name__)

from pyramid.response import Response
from pyramid.renderers import render_to_response
from pyramid.httpexceptions import HTTPFound
from msaf.models import dbsession
from msaf.models.msdb import Sample, Marker, AlleleSet
from msaf.models.queryset import QuerySet, queried_samples
from msaf.lib.querycmd import get_queries, parse_querycmd
from msaf.lib.analysis.summary import summarise_allele
from rhombus.lib.roles import PUBLIC
from rhombus.views import roles

#from webhelpers import paginate

from msaf.lib.querycmd import parse_querycmd, insert_queryset, docs
import transaction

@roles( PUBLIC )
def index(request):

    if not request.GET.get('_method', None) == '_exec':

        markers = Marker.query().order_by( Marker.code )
        queries = get_queries()

        return render_to_response('msaf:templates/analysis/allele/index.mako',
            { 'markers': markers, 'queries': queries },
            request = request )

    queryset = request.GET.get('queryset', '')
    markers = request.GET.getall('markers')
    threshold = int(request.GET.get('threshold', 0) or 0)

    sample_ids = parse_querycmd( queryset )

    results = []
    for marker_id in markers:
        results.append( summarise_allele(sample_ids, marker_id, threshold) )
        
    return render_to_response('msaf:templates/analysis/allele/report.mako',
        { 'results': results, 'queryset': queryset, 'threshold': threshold,
          'sample_size': sample_ids.count(),
          'He': sum( [ r['He'] for r in results ] ) / len(results)
        },
        request=request )

