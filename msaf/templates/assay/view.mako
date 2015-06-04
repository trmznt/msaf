<%inherit file="rhombus:templates/base.mako" />
<%namespace file="msaf:templates/assay/widget.mako" import="show_assay, show_assay_js" />
<%namespace file="msaf:templates/channel/widget.mako" import="list_channels" />
<%namespace file="msaf:templates/allele/widget.mako" import="list_alleles" />

<%namespace file="rhombus:templates/common/form.mako" import="input_text, input_hidden, input_textarea, checkboxes, submit_bar, input_show, textarea_show, button_edit, selection_ek" />

## input: assay, lsp (ladder_scanning_parameter)

<h2>Assay Viewer</h2>

<div class='row'>
<div class='span8'>
  ${show_assay(assay)}
</div>
<div class='span4'>
  ${list_channels(assay.channels)}
</div>
</div>

<div class='row'>
<form method='POST' action='/assay/@@action'>
<input type="hidden" name='assay_id' value="${assay.id}" />
<a role='button' data-target='#ladder_peak_params' href='#ladder_peak_params' class='btn' data-toggle='modal'>Find ladder peaks</a>
<button name='_method' value='estimate_z'>Estimate Z</button>
<button name='_method' value='find_peaks'>Find peaks</button>
</form>

<div id='ladder_peak_params' class="modal hide" role="dialog">
<div class='modal-body'>

<h3>Ladder Peaks Search Parameter</h3>
<form method='POST' action='/assay/@@action'>
${input_hidden('assay_id', value = assay.id)}
${input_text('min_height', 'Minimum Height', value = lsp.min_height)}
${input_text('relative_min', 'Min relative from median height', value = lsp.min_relative_ratio)}
${input_text('relative_max', 'Max relative from median height', value = lsp.max_relative_ratio)}
${submit_bar('Find ladder peaks', 'find_ladder_peaks')}

</form>
</div>
</div>

<div id='peak_params' class="modal hide" role="dialog">
<div class='modal-body'>

<h3>Peaks Search Parameter</h3>
<form method='POST' action='/assay/@@action'>
${input_hidden('assay_id', value = assay.id)}
${input_text('min_height', 'Minimum Height', value = 30)}
${input_text('relative_min', 'Min relative from median height', value = 0.50)}
${input_text('relative_max', 'Max relative from median height', value = 4)}
${submit_bar('Find ladder peaks', 'find_ladder_peaks')}

</form>
</div>
</div>


</div><!-- row -->


<div class='row'>
<div class='span10'>
<div id="placeholder" style="width:800px;height:400px;"></div>
</div>
<div class='span2'>
<p id="choices">Show:</p>
</div>
</div>

<div class='row' style="height:300px;overflow-y:auto">
<div id="allele-modal-view" class="modal hide" role="dialog">
<div class='modal-body'>
</div>
</div>

<div class='span8'>
% for c in assay.channels:
  <p><b>${c.dye} / ${c.marker.code}</b></p>
    % if c.allelesets.count() >= 1:
        ${list_alleles(sorted(c.get_latest_alleleset().alleles, key=lambda x: x.rtime))}
    % endif
  <br />
% endfor
</div></div>
##
##
<%def name="jscode()">
  ${show_assay_js(assay)}
  $('#allele-modal-view').on('hidden', function() {
      $(this).removeData('modal');
    }
  );
</%def>
##
<%def name="jslink()">
<script src="/static/msaf/js/flot/jquery.flot.js"></script>
<script src="/static/msaf/js/flot/jquery.flot.selection.js"></script>
<script src="/assay/${assay.id}@@drawchannels" type="text/javascript"></script>
</%def>
