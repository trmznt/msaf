
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

from msaf.lib.advquerycmd import parse_advquerycmd
from msaf.lib.tools.summary import get_filtered_analytical_sets2


from msaf.lib.tools.distance import pw_distance, nj_tree


@roles( PUBLIC )
def index(request):

    if not request.params.get('_method', None) == '_exec':
        queries = get_queries()

        return render_to_response('msaf:templates/tools/nj/index.mako',
                { 'queries': queries, 'markers': get_marker_list() },
                request = request)


    #parse form

    #baseparams = parse_base_params( request.params )
    #spatial_differentiation = int(request.params.get('spatial_differentiation', 4))
    #temporal_differentiation = int(request.params.get('temporal_differentiation', 0))

    label_modifier_file = request.params.get('labelfile', None)
    label_modifier = {}
    if label_modifier_file:
        buf = label_modifier_file.file.read().decode('UTF-8')
        #lines = label_modifier_file.read().split('\n')
        for line in buf.split('\n'):
            if not line: continue
            old_label, new_label = line.split('\t')
            label_modifier[old_label] = new_label

    baseparams = parse_base_params( request.params )
    spatial_differentiation = int(request.params.get('spatial_differentiation', -1))
    temporal_differentiation = int(request.params.get('temporal_differentiation', 0))

    sample_sets = parse_advquerycmd( baseparams.queryset )
    diff_analytical_sets, sample_report, marker_report = get_filtered_analytical_sets2(
                sample_sets = sample_sets,
                baseparams = baseparams,
                spatial_differentiation = spatial_differentiation,
                temporal_differentiation = temporal_differentiation )


    #sample_ids = parse_querycmd( baseparams.queryset )
    #diff_analytical_sets, sample_report, marker_report = get_filtered_analytical_sets(
    #            sample_ids = sample_ids, marker_ids = baseparams.marker_ids,
    #            allele_absolute_threshold = baseparams.allele_absolute_threshold,
    #            allele_relative_threshold = baseparams.allele_relative_threshold,
    #            sample_quality_threshold = baseparams.sample_quality_threshold,
    #            marker_quality_threshold = baseparams.marker_quality_threshold,
    #            spatial_differentiation = spatial_differentiation,
    #            temporal_differentiation = temporal_differentiation )

    base_pwdist = pw_distance( diff_analytical_sets )
    if label_modifier:
        base_pwdist.modify_labels( label_modifier )

    temp_dir = fso.mkranddir('/temps')
    nj_file = nj_tree( base_pwdist, temp_dir.rpath, 'png')
    nj_pdf = nj_tree( base_pwdist, temp_dir.rpath, 'pdf')

    vpath_nj = fso.get_urlpath( nj_file )
    vpath_nj_pdf = fso.get_urlpath( nj_pdf )

    return render_to_response('msaf:templates/tools/nj/report.mako',
            { 'vpath_nj': vpath_nj, 'vpath_nj_pdf': vpath_nj_pdf },
            request = request )

