<%namespace file="rhombus:templates/common/selection_bar.mako" import="selection_bar, selection_bar_js" />
<%namespace file="rhombus:templates/common/form.mako" import="input_text, input_hidden, input_textarea, checkboxes, submit_bar, input_show, textarea_show, button_edit, button" />
<%namespace file='rhombus:templates/group/widget.mako' import='select_group_js' />

##
<%def name="list_batches(batches)">
<form method='post' action='${request.route_url("msaf.batch-action")}'>
${selection_bar('batch', ('Add New Batch', request.route_url("msaf.batch-edit", id=0)))}
<table id="batch-list" class="table table-striped table-condensed">
<thead><tr><th></th><th>Batch Code</th><th>Samples</th><th>Group</th><th>Status</th></tr></thead>
<tbody>
% for b in batches:
    <tr><td><input type="checkbox" name="batch-ids" value='${b.id}' /> </td>
        <td><a href="${request.route_url('msaf.batch-view', id=b.id)}">${b.code}</a></td>
        <td><a href="${request.route_url('msaf.sample', _query={ 'batch_id': b.id })}">${b.samples.count()}</a></td>
        <td>${b.group.name}</td>
        <td>${'PUB' if b.published else 'UNPUB'} ${'SHARED' if b.shared else 'UNSHARED'}</td>
    </tr>
% endfor
</tbody>
</table>
</form>
</%def>


##
<%def name="list_batches_js()">
  ${selection_bar_js("batch", "batch-ids")}
</%def>


##
<%def name="show_batch(batch)">
  <form class='form-horizontal'>
    <fieldset>
      ${input_show('Batch Code', batch.code)}
      ${input_show('Group Owner', batch.group.name)}
      ${textarea_show('Description', batch.desc)}
      ${input_show('Published', 'Yes' if batch.published else 'No')}
      ${input_show('Shared', 'Yes' if batch.shared else 'No')}
      ${button_edit('Edit', request.route_url('msaf.batch-edit', id=batch.id))}
    </fieldset>
  </form>
</%def>

##
##
<%def name="show_batch(batch)">
  <table class='table table-condensed'>
  <tr><td class='text-right'>Batch Code : </td><td>${batch.code}</td></tr>
  <tr><td class='text-right'>Group Owner : </td><td>${batch.group.name}</td></tr>
  <tr><td class='text-right'>Description : </td><td>${batch.desc}</td></tr>
  <tr><td class='text-right'>Status :</td>
        <td>${'Published' if batch.published else 'Unpublished'}
            ${'Shared' if batch.shared else 'Unshared'}
        </td></tr>
    <tr><td></td>
        <td>${button('Edit', request.route_url('msaf.batch-edit', id=batch.id),
                'icon-edit icon-white')}
            ${button('Generate Report',
                request.route_url('tools-report', _query = { 'batchcode': batch.code }),
                'icon-book icon-white')}
        </td></tr>
  </table>

</%def>


##
<%def name="edit_batch(batch)">
<form class='form-horizontal' method='post'
        action='${request.route_url("msaf.batch-save", id=batch.id)}' >
  <fieldset>
    ${input_text('msaf-batch_code', 'Batch code', value = batch.code)}
    ${input_hidden('msaf-batch_group_id', 'Primary group', class_span="input-xlarge",
            value=batch.group_id)}
    ${input_hidden('msaf-assay_provider_id', 'Assay provider group', class_span="input-xlarge",
            value=batch.assay_provider_id)}
    ${input_textarea('msaf-batch_desc', 'Description', value = batch.desc)}
    ${submit_bar()}
  </fieldset>
</form>
</%def>

##
<%def name="edit_batch_js(batch)">
  ${select_group_js('#msaf-batch_group_id')}
  ${select_group_js('#msaf-assay_provider_id')}
  
% if batch.group:
    $('#msaf-batch_group_id').select2("data", { id: '${batch.group.id}', text: '${batch.group.name}' });
    $('#msaf-assay_provider_id').select2("data", { id: '${batch.group.id}', text: '${batch.group.name}' });

% endif
</%def>
