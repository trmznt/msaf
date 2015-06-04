<%inherit file="rhombus:templates/base.mako" />
<%namespace file='msaf:templates/queryset/common.mako'
  import='show_queries' />
<%namespace file='rhombus:templates/common/form.mako'
  import='input_text, selection' />
##
## local vars: queries, markersets
##
<div class='row'>

  <div class='span9'>
    <h3>Allele Summary</h3>
    <form method='get' class='form-horizontal'>
      <fieldset>
        ${input_text('queryset', 'Query set', class_span='span5')}
        ${selection('markers', 'Select marker(s)',
            [ (x.id, x.code) for x in markers ], multiple=True )}
        ${input_text('threshold', 'Threshold', class_span='span1')}
        <div class='form-actions'>
          <button class='btn btn-primary' type='submit' name='_method' value='_exec'>Analyse</button>
        </div>
      </fieldset>
    </form>    

  </div>


  <div class='span3'>
    ${show_queries(queries)}
  </div>

</div>


