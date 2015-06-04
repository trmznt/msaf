
<%inherit file="rhombus:templates/base.mako" />
<%namespace file='msaf:templates/queryset/common.mako'
  import='show_queries' />
<%namespace file='rhombus:templates/common/form.mako'
  import='input_text, selection, submit_bar' />
<%namespace file='msaf:templates/tools/queryforms.mako'
  import='query_fields, differentiation_fields, ctrl_fields' />


<div class='row'>

  <div class='span9'>
    <h3>Allele Summary</h3>

    <ul class="nav nav-tabs" id="formTab">
      <li class="active"><a href="#generalform" data-toggle="tab">Form query</a></li>
      <li><a href="#advctrl" data-toggle="tab">Script query</a></li>
    </ul>

    <div class="tab-content">
    <div class="tab-pane active" id="generalform">
    <form method='get' class='form-horizontal'>
      <fieldset>
        ${query_fields(markers)}
        ${differentiation_fields()}

        ${submit_bar('Summarize Allele', '_exec')}
      </fieldset>
    </form>
    </div>
    <div class="tab-pane" id="advctrl">
    <form method='get' class='form-horizontal'>
      <fieldset>
        ${ctrl_fields()}

        ${submit_bar('Summarize Allele', '_yamlexec')}
      </fieldset>
    </form>
    </div>
    </div>
  </div>


  <div class='span3'>
    ${show_queries(queries)}
  </div>

</div>

