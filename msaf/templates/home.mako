<%inherit file="rhombus:templates/base.mako" />
<%namespace file="${context.get('request').get_resource('custom.hero', 'msaf:templates/custom/hero.mako')}" import="hero" />
<%namespace file="${context.get('request').get_resource('custom.doclinks', 'msaf:templates/custom/doclinks.mako')}" import="doclinks" />

<div class='row'>
    <div class='span9'>
    ${hero()}
    </div>
    <div class='span3'>
% if not request.authenticated():
        <!-- login box -->
        ${loginbox()}
% else:
        <!-- documentation box -->
        ${doclinks()}
% endif
    </div>
</div>
<div class='row'>
  <div class='span4'>
    <h3>Browse the Data</h3>
    <p>Browse batches, samples, locations, markers and alleles by choosing from Browse menu.</p>
    <p>Generate a report on your batches by browsing to the batch and click on Generate Report button</p>
  </div>
  <div class='span4'>
    <h3>Perform Analysis</h3>
    <p>Use Tools menu to choose the analysis you would like to perform in your dataset.</p>
    <p>Prepare your dataset for the analysis using Query Syntax Tool or Query Wizard inside
    Tools menu</p>
  </div>
  <div class='span4'>
    <h3>Upload Your Data</h3>
    <p>Perform batch uploading from your prepared CSV, tab-delimited, JSON or YAML format file
    using Upload Data menu</p>
  </div>
</div>
##
##
<%def name='loginbox()'>
    <div class="login-form">
        <h2>Login</h2>
        <form action="/login" method="post">
            <fieldset>
                <div class="clearfix">
                    <label>Username</label>
                    <input type="text" name='username' class='span2'>
                </div>
                <div class="clearfix">
                    <label>Password</label>
                    <input type="password" name='password' class='span2'>
                </div>
                <button class="btn btn-primary" type="submit">Sign in</button>
            </fieldset>
        </form>
    </div>
</%def>
##
##
