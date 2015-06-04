<%inherit file="rhombus:templates/base.mako" />
<%namespace file='msaf:templates/queryset/common.mako'
  import='show_queries' />
<%namespace file='rhombus:templates/common/form.mako'
  import='input_text, selection' />
##
## local vars: queries, markers
##
<div class='row'>

  <div class='span9'>
    <h3>Data Export</h3>
    <form method='get' class='form-horizontal'>
      <fieldset>
        ${input_text('queryset', 'Query set', class_span='span5',
                value = request.params.get('queryset', ''))}
        ${input_text('threshold', 'Threshold', class_span='span1',
                value = request.params.get('threshold', '100 | 33%'))}
        ${selection('markers', 'Select marker(s)',
            [ (m_id, m_text) for (m_text, m_id) in markers ], multiple=True )}
        ${input_text('filename', 'Filename', class_span='span4',
                value = request.params.get('filename', ''))}
        ${selection('fmt', 'File format',
            [   ('flat', 'Flat type (LIAN, GENEPOP)'),
                ('arq', 'Arlequin'),
                ('yaml-allele', 'Alleles (YAML)')
            ], multiple=False )}

        <div class='form-actions'>
          <button class='btn btn-primary' type='submit' name='_method' value='_exec'>Export Data</button>
        </div>
      </fieldset>
    </form>    

  </div>


  <div class='span3'>
    ${show_queries(queries)}
  </div>

</div>


