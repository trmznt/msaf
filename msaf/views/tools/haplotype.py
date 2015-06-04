
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
from msaf.lib.tools.summary import get_filtered_analytical_sets
from msaf.views.utils import get_marker_list, parse_base_params

# analysis spesific imports

from msaf.lib.tools.haplotype import summarize_haplotypes, plot_haplotype


@roles( PUBLIC )
def index(request):

    if not request.GET.get('_method', None) == '_exec':
        queries = get_queries()

        return render_to_response('msaf:templates/tools/haplotype/index.mako',
                { 'queries': queries, 'markers': get_marker_list() },
                request = request)


    #parse form

    baseparams = parse_base_params( request.GET )
    spatial_differentiation = int(request.GET.get('spatial_differentiation', 4))
    temporal_differentiation = int(request.GET.get('temporal_differentiation', 0))


    sample_ids = parse_querycmd( baseparams.queryset )
    diff_analytical_sets, sample_report, marker_report = get_filtered_analytical_sets(
                sample_ids = sample_ids, marker_ids = baseparams.marker_ids,
                allele_absolute_threshold = baseparams.allele_absolute_threshold,
                allele_relative_threshold = baseparams.allele_relative_threshold,
                allele_relative_cutoff = baseparams.allele_relative_cutoff,
                sample_quality_threshold = baseparams.sample_quality_threshold,
                marker_quality_threshold = baseparams.marker_quality_threshold,
                spatial_differentiation = spatial_differentiation,
                temporal_differentiation = temporal_differentiation )

    (unique_haplotype, haplotype_freqs, total_freqs, haplotype_df) = summarize_haplotypes(
                                diff_analytical_sets )

    # create the histogram

    temp_dir = fso.mkranddir('/temps')
    plot_file = plot_haplotype( haplotype_df, temp_dir.rpath, 'haplotypes_stacked.png' )
    vpath_plot = fso.get_urlpath( plot_file )

    return render_to_response('msaf:templates/tools/haplotype/report.mako',
            {   'unique_haplotype': unique_haplotype,
                'haplotype_freqs': haplotype_freqs,
                'vpath_plot': vpath_plot },
            request = request )

