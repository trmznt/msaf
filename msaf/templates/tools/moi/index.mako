<%inherit file="rhombus:templates/base.mako" />
<%namespace file='msaf:templates/queryset/common.mako'
  import='show_queries' />
<%namespace file='rhombus:templates/common/form.mako'
  import='input_text, selection' />
<%namespace file='msaf:templates/tools/queryforms.mako'
  import='query_fields, differentiation_fields' />


<div class='row'>

  <div class='span9'>
    <h3>MoI - Multiplicity of Infection</h3>
    <form method='get' class='form-horizontal'>
      <fieldset>
        ${query_fields(markers)}
        ${differentiation_fields()}


        <div class='form-actions'>
          <button class='btn btn-primary' type='submit' name='_method' value='_exec'>Generate MoI</button>
        </div>
      </fieldset>
    </form>
  </div>


  <div class='span3'>
    ${show_queries(queries)}
  </div>

</div>

