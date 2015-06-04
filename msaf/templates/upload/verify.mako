<%inherit file="rhombus:templates/base.mako" />
<%namespace file="rhombus:templates/common/form.mako" import="input_text, input_textarea, selection, checkboxes" />


<h2>Upload Data</h2>
<h3>Step 2: Save to Database</h3>

<p>Your file [<b>${filename}</b>] has been parsed and analysed by the system.
% if report_log:
However, you need to check the log below as the system found some minor problem with your input file.
% endif
</p>

<form class="form-horizontal" method="post" enctype="multipart/form-data"
    action="/upload/commit">
    <fieldset>
        <input type="hidden" name="ticket" value="${ticket}" />
        ${input_text('batch_code', 'Batch code')}
        ${input_textarea('desc', 'Short description (optional)')}
        ${selection('group', 'Group owner',
            [ (g.id, g.name) for g in request.userinstance().get_groups() ])}
        ${selection('assay_provider', 'Group for assay provider',
            [ (g.id, g.name) for g in request.userinstance().get_groups() ])}
        ${checkboxes('options', 'Options',
            [   ('opt_update_sample', 'add new samples on existing batch code', False),
                ('opt_update_allele', 'add, update or replace existing alleles', False),
                ('opt_share', 'share samples and alleles', False),
                ('opt_update_info', 'update sample information only', False) 
            ] ) }
        <div class="form-actions">
            <p>You can continue to proceed to next step to actually save your data to the database, or download the converted JSON file for manual inspection.</p>
            <button class="btn btn-primary" type="submit" name="_method" value="commit">
                Continue
            </button>
            <button class="btn" type="submit" name="_method" value="view_json">
                Download JSON
            </button>
            <button class="btn">Cancel</button>
        </div>
    </fieldset>
</form>



% if report_log:
<p>The submitted CSV/JSON file contains the following warnings:</p>
<pre>
${report_log}
</pre>

% endif

