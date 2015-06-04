<%namespace file="rhombus:templates/common/selection_bar.mako" import="selection_bar, selection_bar_js" />
<%namespace file="rhombus:templates/common/form.mako" import="input_text, input_hidden, input_textarea, checkboxes, submit_bar, input_show, textarea_show, button_edit, selection_ek" />

##
<%def name="list_alleles(alleles)">
<table id='allele-list' class='table table-striped table-condensed'>
<thead><tr>
  <th>Allele</th><th>Size</th><th>RTime</th>
  <th>Height</th><th>Area</th><th>Boundary</th><th>Beta</th>
  <th>Type</th><th></th>
<tr></thead>
<tbody>
<%
  kwargs = { 'data-toggle':'modal', 'data-target':'#allele-modal-view' }
%>
% for a in alleles:
  <tr><td>${a.value}</td><td>${'%03.2f' % a.size}</td><td>${'%05d' % a.rtime}</td>
      <td>${'%05d' % a.height}</td><td>${a.area}</td>
      <td>${'%05d - %05d' % (a.brtime, a.ertime)}</td><td>${'%02.3f' % a.beta}</td>
      <td>${a.type}</td>
      <td>${h.link_to( 'Edit', request.route_url('msaf.assay-action', _query=dict(_method='edit_allele', id=a.id)), **kwargs )}</td>
  </tr>
% endfor
</tbody></table>
</%def>
##
##
##
<%def name="list_alleles_column(allele_list)">
<div class="row">
  % for (marker, alleles) in allele_list:
    % if marker != 'undefined':
    <div class='span1'>
        <b>${marker}</b><br />
        % for (v, h) in alleles:
          ${'%3.1f / %d' % (v, h)}<br />
        % endfor
    </div>
    % endif
  % endfor
</div>
</%def>
#
#
#
<%def name="edit_allele(allele)">
<form class='form-horizontal form-condensed' method='post'
    action='${request.route_url("msaf.assay-action", _query=dict(_method="save_allele",
                    id=allele.id))}'>
  <fieldset>
    ${input_hidden('msaf.allele_id', value = allele.id)}
    ${input_show('Dye', allele.alleleset.channel.dye)}
    ${input_show('Marker', allele.alleleset.marker.code)}
    ${input_show('Method', allele.method)}
    ${input_text('msaf.allele_value', 'Value', value=allele.value)}
    ${input_text('msaf.allele_size', 'Size', value=allele.size)}
    ${input_text('msaf.allele_rtime', 'Retention time', value=allele.rtime)}
    ${input_text('msaf.allele_height', 'Height', value=allele.height)}
    ${input_text('msaf.allele_area', 'Area', value=allele.area)}
    ${selection_ek('msaf.allele_type_id', 'Type', '@PEAK-TYPE', value=allele.type_id)}
    ${submit_bar('Update allele', 'update_allele')}
  </fieldset>
</form>
</%def>
