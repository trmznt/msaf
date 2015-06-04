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
from msaf.configs import get_proc_path

import os

@roles( PUBLIC )
def index(request):

    if not request.GET.get('_method', None) == '_exec':

        # this can be put into function
        markersets = MarkerSet.query().order_by( MarkerSet.name )
        queries = get_queries()

        return render_to_response('msaf:templates/analysis/phylogenetics/index.mako',
            { 'markersets': markersets, 'queries': queries },
            request = request )

    queryset = request.GET.getall('queryset')
    markers = request.GET.getall('markers')
    threshold = int(request.GET.get('threshold', 0) or 0)

    labels = request.GET.getall('labels')

    all_samples = []
    all_labels = []
    for q, l in zip(queryset, labels):

        sample_ids = parse_querycmd( q )

        genotype = dominant_genotype( sample_ids, markers, threshold )

        for g in genotype.itervalues():
            all_samples.append( g )
            all_labels.append( l )

    # calculate Distance
    dist = distance_pair( all_samples )

    proc_path = get_proc_path()
    os.mkdir( proc_path )

    dist_out = open( proc_path + '/distance', 'w')
    print >> dist_out, "%d" % len(dist)
    for i in range(len(dist)):
        print >> dist_out, "%-10s  %s" % ( all_labels[i], "  ".join( ["%5.4f" % x for x in dist[i] ] ) )
    dist_out.close()

    #pipe = Popen("", shell=True, bufsize=bufsize, stdin=PIPE).stdin

    raise RuntimeError



def distance_pair( m ):
    """ return a distance matrix """

    # prepare zero matrix
    L = len(m)
    D = []
    for i in range(L):
        D.append( [0.0] * L )

    # calculate distance
    n = len(m[i])
    for i in range(L):
        for j in range(i, L):
            ps = len( filter( lambda x: x[0] == x[1], zip(m[i], m[j]) ) )

            D[i][j] = D[j][i] = 1.0 - 1.0 * ps/n
            

    return D








