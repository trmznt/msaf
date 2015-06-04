
# mandatory imports

import logging

log = logging.getLogger(__name__)

from pyramid.response import FileResponse
from pyramid.renderers import render_to_response
from pyramid.httpexceptions import HTTPFound

from rhombus.lib.roles import PUBLIC
from rhombus.views import roles
from rhombus.views.errors import error_page
from rhombus.lib import fsoverlay as fso

from msaf.lib.querycmd import parse_querycmd, get_queries
from msaf.lib.analytics import group_samples, get_sample_ids
from msaf.lib.tools.summary import get_filtered_analytical_sets, summarize_markers
from msaf.views.utils import get_marker_list, parse_base_params

from matplotlib import pyplot as plt

import numpy as np


@roles( PUBLIC )
def index(request):

    if not request.GET.get('_method', None) == '_exec':
        queries = get_queries()

        return render_to_response('msaf:templates/tools/moi/index.mako',
                { 'queries': queries, 'markers': get_marker_list() },
                request = request)


    #parse form

    baseparams = parse_base_params( request.GET )
    spatial_differentiation = int(request.GET.get('spatial_differentiation', 0))
    temporal_differentiation = int(request.GET.get('temporal_differentiation', 0))


    #sample_ids = parse_querycmd( baseparams.queryset )
    #diff_analytical_sets, sample_report, marker_report = get_filtered_analytical_sets(
    #            sample_ids = sample_ids, marker_ids = baseparams.marker_ids,
    #            allele_absolute_threshold = baseparams.allele_absolute_threshold,
    #            allele_relative_threshold = baseparams.allele_relative_threshold,
    #            sample_quality_threshold = baseparams.sample_quality_threshold,
    #            marker_quality_threshold = baseparams.marker_quality_threshold,
    #            spatial_differentiation = spatial_differentiation,
    #            temporal_differentiation = temporal_differentiation )

    sample_sets = parse_advquerycmd( baseparams.queryset )
    diff_analytical_sets, sample_report, marker_report = get_filtered_analytical_sets2(
                sample_sets = sample_sets,
                baseparams = baseparams,
                spatial_differentiation = spatial_differentiation,
                temporal_differentiation = temporal_differentiation )



    temp_dir = fso.mkranddir( '/temps' )
    figures = []
    for idx, analytical_set in enumerate(diff_analytical_sets):
        moi_alleles = [ x[1] for x in analytical_set.calculate_moi().values() ]
        values = [ 0 ]  * 4
        for x in moi_alleles:
            if x == 0: continue
            values[x] += 1

        #raise RuntimeError( moi_alleles )
        hist_file = temp_dir.rpath + 'moi-hist-%0d.png' % idx
        fig = plt.figure()
        ax = fig.add_subplot(111)
        idx = np.arange(len(values)-1)
        ax.bar( idx, values[1:] )

        axes = ax
        positions = idx
        axes.spines['right'].set_color('none')
        axes.spines['top'].set_color('none')
        axes.xaxis.set_ticks_position('bottom')

        # was: axes.spines['bottom'].set_position(('data',1.1*X.min()))
        axes.spines['bottom'].set_position(('axes', -0.05))
        axes.yaxis.set_ticks_position('left')
        axes.spines['left'].set_position(('axes', -0.05))

        axes.set_xlim([np.floor(positions.min()), np.ceil(positions.max())])
        axes.set_ylim([0,max(values) + 10])

        ax.set_xticks( idx + 0.5 )
        ax.set_xticklabels( [ str(x) for x in range(1, len(values)) ] )

        axes.xaxis.grid(False)
        axes.yaxis.grid(False)
        fig.tight_layout()
        fig.savefig( hist_file )
        figures.append( fso.get_urlpath( hist_file ) )


    #temp_dir = fso.mkranddir( '/temps' )
    #pca_file = plot_pca( base_pca, base_pwdist, temp_dir.rpath, "base-pca.png" )
    #vpath_basepca = fso.get_urlpath( pca_file )

    return render_to_response('msaf:templates/tools/moi/report.mako',
            { 'figures': figures },
            request = request )



