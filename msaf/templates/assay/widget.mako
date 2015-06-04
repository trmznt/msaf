<%namespace file="rhombus:templates/common/selection_bar.mako" import="selection_bar, selection_bar_js" />
<%namespace file="rhombus:templates/common/form.mako" import="input_text, input_hidden, input_textarea, checkboxes, submit_bar, input_show, textarea_show, button_edit, selection_ek" />


##
<%def name="list_assays(assays)">
<form method='post' action='${request.route_url("msaf.assay-action")}'>
${selection_bar('assay', others='<button id="add-assay" type="button" class="btn btn-mini btn-success">Add assay</button>')}

<table id='assay-list' class='table table-striped table-condensed'>
<thead><tr>
  <th></th>
  <th>Assay Filename</th>
  <th>Score</th>
  <th>RSS</th>
  <th>Marker</th>
</tr></thead>
<tbody>
% for a in assays:
  <tr><td><input type="checkbox" name="assay-ids" value="${a.id}" /> </td>
      <td><a href="${request.route_url('msaf.assay-view', id=a.id)}">${a.filename}</a></td>
      <td>${'%1.2f' % a.score}</td>
      <td>${'%4.2f' % a.rss}</td>
      <td>${' | '.join( sorted( m.marker.code for m in a.markers if m.marker.code != 'undefined' ) )}</td>
  </tr>
% endfor
</tbody></table>
</form>
</%def>

## list_assays_js: sample: current sample for adding new assay
<%def name="list_assays_js(sample)">
  $('#add-assay').upload( { 
    name: 'assay_file',
    action: '${request.route_url("msaf.sample-action")}',
    params: { _method: 'add-assay', sample_id: '${sample.id}' },
    onComplete: function (response) {
        var resp = jQuery.parseJSON( response );
        window.location.replace( resp['url'] );
      }
    }
  );

  ${selection_bar_js("assay", "assay-ids")}
</%def>

##
<%def name="edit_assay(assay, sample=None)">
<form class='form-horizontal' method='post'
    action='${request.route_url("msaf.assay-save", id=assay.id)}'>
  <fieldset>
    ${input_hidden('msaf-assay_id', value=assay.id)}
    ${input_show('Filename', assay.filename)}
    ${selection_ek('msaf-assay.panel_id', 'Panel', '@PANEL', value = assay.panel_id)}
    ${selection_ek('msaf-assay.size_standard_id', 'Ladder', '@LADDER', value = assay.size_standard_id)}
    ${submit_bar()}
  </fieldset>
</form>
</%def>

##
<%def name="edit_assay_js(assay)">
</%def>

##
<%def name="show_assay(assay)">
<form class='form-horizontal form-condensed'>
  <fieldset>
    ${input_hidden('msaf-assay_id', value=assay.id)}
    ${input_show('Sample', h.link_to(assay.sample.code,
                    request.route_url('msaf.sample-view', id=assay.sample.id)))}
    ${input_show('Filename', assay.filename)}
    ${input_show('Panel', assay.panel)}
    ${input_show('Ladder', assay.size_standard)}
    ${input_show('Status', assay.status)}
  % if assay.z is not None:
    ${input_show('Z params:', str(assay.z))}
    ${input_show('RSS:', assay.rss)}
    ${input_show('Score:', assay.score)}
    ${input_show('QC report:', assay.strings.get('qcreport', ''))}
  % endif
    ${button_edit('Edit', request.route_url('msaf.assay-edit', id=assay.id))}
  </fieldset>
</form>
</%def>

##
<%def name="show_assay_js(assay)">
</%def>

##
<%def name="drawchannels_jslink(assay_id)">
<script src="/static/js/flot/jquery.flot.js" />
<script src="/assay/${assay_id}@@drawchannels" type="text/javascript" />
</%def>

##

