<%inherit file="rhombus:templates/base.mako" />
<%namespace file="rhombus:templates/common/form.mako" import="input_text" />

<h2>Upload data</h2>
<h3>Step 1: Verify File</h3>

<p>Data uploading is a 2-step process. The first step is to check the consistency of the format of the input file. Any problems with your input file will be reported. The second step is to commit your data into the database.</p>

<form class="form-horizontal" method="post" enctype="multipart/form-data"
    action="/upload/verify">
    <fieldset>
        <div class="control-group">
            <label class="control-label" for="input_file">File input</label>
            <div class="controls">
                <input type="file" class="input-xlarge" id="input_file" name="input_file" />
                <p class="help-block">File input should be in CSV or JSON format.</p>
            </div>
        </div>
        <div class="form-actions">
            <button class="btn btn-primary" type="submit" name="_method" value="verify">
                Continue
            </button>
            <button class="btn">Cancel</button>
        </div>
    </fieldset>
</form>
