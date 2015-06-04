
<%inherit file="rhombus:templates/base.mako" />
<%namespace file='msaf:templates/queryset/common.mako'
  import='show_queries' />
<%namespace file='rhombus:templates/common/form.mako'
  import='input_text, selection, submit_bar' />
<%namespace file='msaf:templates/tools/queryforms.mako'
  import='query_fields, differentiation_fields' />


<div class='row'>

  <div class='span9'>
    <h3>Haplotype Summary</h3>
    <form method='get' class='form-horizontal'>
      <fieldset>
        ${query_fields(markers)}
        ${differentiation_fields()}

        ${submit_bar('Summarize Haplotypes', '_exec')}
      </fieldset>
    </form>
  </div>


  <div class='span3'>
    ${show_queries(queries)}
  </div>

</div>

