<%namespace file="rhombus:templates/common/selection_bar.mako" import="selection_bar, selection_bar_js" />
<%namespace file="rhombus:templates/common/form.mako" import="input_text, input_hidden, input_textarea, checkboxes, submit_bar, input_show, textarea_show, button_edit, selection_ek" />


#
#
<%def name="list_markers(markers)">
<form method='post' action='${request.route_url("msaf.marker-action")}'>
${selection_bar('marker', ('Add Marker', request.route_url("msaf.marker-edit", id=0)))}

<table id='marker-list' class='table table-striped table-condensed'>
<thead><tr><th></th><th>Marker Code</th><th>Locus</th><th>Species</th><th>Repeats</th>
    <th>Min Size</th><th>Max Size</th></tr>
<tbody>
% for m in markers:
  <tr><td><input type="checkbox" name="marker-ids" value="${m.id}" /></td>
      <td><a href="${request.route_url('msaf.marker-view', id=m.id)}">${m.code}</a></td>
      <td>${m.locus}</td>
      <td>${m.species}</td>
      <td class='text-right'>${m.repeats}</td>
      <td class='text-right'>${m.min_size}</td>
      <td class='text-right'>${m.max_size}</td>
  </tr>
% endfor
</tbody></table>
</form>
</%def>

#
#
<%def name="list_markers_js()">
    ${selection_bar_js("marker", "marker-ids")}
</%def>

#
#
<%def name="show_marker(marker)">
  <form class="form-horizontal form-condensed">
    <fieldset>
      ${input_show('Marker code', marker.code)}
      ${input_show('Locus', marker.locus)}
      ${input_show('1st Primer Pair', marker.primer_1)}
      ${input_show('2nd Primer Pair', marker.primer_2)}
      ${input_show('Repeats', marker.repeats)}
      ${input_show('Species', marker.species)}
      ${input_show('Description', marker.desc)}
      ${input_show('Minimum Size', marker.min_size)}
      ${input_show('Maximum Size', marker.max_size)}
      ${input_show('Bins', marker.bins)}
      ${button_edit('Edit', request.route_url('msaf.marker-edit', id=marker.id))}
    </fieldset>
  </form>
</%def>

#
#
<%def name="edit_marker(marker)">
<form class="form-horizontal form-condensed"
        method='POST'
        action='${request.route_url("msaf.marker-save", id=marker.id)}' >
  <fieldset>
    ${input_hidden('msaf/marker.id', '', value=marker.id)}
    ${input_text('msaf/marker.code', 'Marker Code', value=marker.code)}
    ${input_text('msaf/marker.locus', 'Locus', value=marker.locus)}
    ${input_text('msaf/marker.species', 'Species', value=marker.species)}
    ${input_text('msaf/marker.repeats', 'Repeats', value=marker.repeats)}
    ${input_text('msaf/marker.min_size', 'Minimum Size', value=marker.min_size)}
    ${input_text('msaf/marker.max_size', 'Maximum Size', value=marker.max_size)}
    ${input_text('msaf/marker.bins', 'Bins', value=marker.bins)}
    ${submit_bar()}
  </fieldset>
</form>
</%def>
