<%inherit file='vivaxdi:templates/base.mako' />
<%namespace file='vivaxdi:templates/commonforms.mako'
    import='input_text, input_textarea, selection, checkboxes, selection_ck, input_hidden' />


##
## sample is existing sample or empty sample
##
<h2>Sample Editor</h2>
<div class='row'>
  <div class='span12'>
    <form class='form-horizontal' method='post'
        action='${request.route_url("vivaxdi.sample-save", id=sample.id)}' >
      <fieldset>
        ${input_text('batch_code', 'Batch code', value = batch.code)}
        ${input_text('subject.name', 'Subject Name', value = subject.name)}
        ${input_text('subject.yearofbirth', 'Year of Birth', value=subject.yearofbirth)}
        ${input_text('subject.gender', 'Gender', value = subject.gender)}
        ${input_text('subject.notes', 'Notes', value=subject.notes)}
        ${input_hidden('batch_id', '', value = batch.id)}
        ${input_text('name', 'Sample Name', value=sample.name)}
        ${input_text('collection_date', 'Collection Date', value=sample.collection_date)}
        ${checkboxes('', '',
            [   ('passive_case_detection', 'Passive Detection', 1,
                    sample.passive_case_detection),
                ('recurrent', 'Recurrent', 1, sample.recurrent) ])}
        ${input_text('type_id', 'Type', value = sample.type_id)}
        ${selection_ck('storage_id', 'Storage Type', '@BLOOD_STORAGE',
                        value = sample.storage_id)}
        ${selection_ck('method_id', 'Method Type', '@METHOD', value = sample.method_id)}
        ${input_text('microscopy_ident', 'Microscopic Detection', value = sample.microscopy_ident)}
        ${input_text('pcr_ident', 'PCR Detection', value = sample.pcr_ident)}
        ${input_text('pcr_method', 'PCR Method', value = sample.pcr_method)}
        ${input_text('comments', 'Comments', value = sample.comments)}
        ${input_hidden('location_id', 'Location', class_span='span7', value = sample.location_id)}
        <div class='form-actions'>
          <button class='btn btn-primary' type='submit' name='_method' value='save'>Save</button>
          <button class='btn' type='reset'>Reset</button>
        </div>
      </fieldset>
    </form>
  </div>
</div>
##
##
<%def name="jscode()">
  $('#location_id').select2( {
        minimumInputLength: 3,
        ajax: {
            url: "/location/lookup",
            dataType: 'json',
            data: function (term, page) {
                return { q: term };
            },
            results: function (data, page) {
                return { results: data };
            }
        }
    });

% if sample.location_id and sample.location_id > 0:
  $('#location_id').select2("val", { id: ${sample.location.id}, text: ${sample.location.render()} })
% endif
</%def>
##
##
<%def name='add_assay(assay=None)' >

</%def>
##
##
<%def name='add_marker(marker=None)' >

</%def>

