<%namespace file="rhombus:templates/common/selection_bar.mako" import="selection_bar, selection_bar_js" />
<%namespace file="rhombus:templates/common/form.mako" import="input_text, input_hidden, input_textarea, checkboxes, submit_bar, input_show, textarea_show, button_edit, selection_ek" />

##
<%def name="list_channels(channels)">
<form method='post' action='${request.route_url("msaf.channel-action")}'>
${selection_bar('channel')}

<table id='channel-list' class='table table-striped table-condensed'>
<thead><tr>
  <th></th>
  <th>Wavelen</th>
  <th>Dye</th>
  <th>Status</th>
</tr></thead>
<tbody>
% for c in channels:
  <tr><td><input type="checkbox" name="channel-ids" value="${c.id}" /> </td>
      <td><a href="${request.route_url('msaf.channel-view', id=c.id)}">${c.wavelen}</a></td>
      <td>${c.dye}</td>
      <td>${c.status}</td>
  </tr>
% endfor
</tbody></table>
</form>
</%def>

##
<%def name="list_channels_js()">
</%def>

##
<%def name="draw_channel(container, url)">

</%def>


