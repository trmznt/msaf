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
    <h3>Report Generator</h3>
    <form method='get' class='form-horizontal'>
      <fieldset>
        ${input_text('batchcode', 'Batch code', class_span='span5',
                value=request.params.get('batchcode', ''))}
        ${input_text('queryset', 'Query set', class_span='span5',
                value = request.params.get('queryset', ''))}
        ${selection('markers', 'Select marker(s)', markers, multiple=True)}
        ${input_text('allele_absolute_threshold', 'Allele absolute threshold',
                class_span='span1',
                value = request.params.get('allele_absolute_threshold', '100'))}
        ${input_text('allele_relative_threshold', 'Allele relative threshold',
                class_span='span1',
                value = request.params.get('allele_relative_threshold', '0.33'))}
        ${input_text('allele_relative_cutoff', 'Allele relative cutoff',
                class_span='span1',
                value = request.params.get('allele_relative_cutoff', '0'))}
        ${input_text('sample_quality_threshold', 'Sample quality threshold',
                class_span='span1',
                value = request.params.get('sample_quality_threshold', '0.50'))}
        ${input_text('marker_quality_threshold', 'Marker quality threshold',
                class_span='span1',
                value = request.params.get('marker_quality_threshold', '0.10'))}
        ${selection('format', 'Report format',
            [ ('pdf', 'PDF'), ('zip', 'zipped file (PDF, images and TeX source)') ], multiple=False )}
        ${selection('location_level', 'Location detailed level',
            [   ('4', '4th Administration Level'),
                ('3', '3rd Administration Level'),
                ('2', '2nd Administration Level'),
                ('1', '1st Administration Level'),
                ('0', 'Country Level'),
                ('-1', 'None')
            ] )}
        ${selection('spatial_differentiation', 'Spatial differentiation by',
            [   ('4', '4th Administration Level'),
                ('3', '3rd Administration Level'),
                ('2', '2nd Administration Level'),
                ('1', '1st Administration Level'),
                ('0', 'Country Level'),
                ('-1', 'None')
            ] )}
        ${selection('temporal_differentiation', 'Temporal differentiation by',
            [   ('0', 'None'),
                ('1', 'Year')
            ] )}
        ${selection('detection_differentiation', 'Detection differentiation',
            [   ('0', 'No'),
                ('1', 'Yes')
            ] )}
        ${selection('njtree', 'NJ tree drawing type',
            [ ('u', 'Unrooted') ] )}
            

        <div class='form-actions'>
          <button class='btn btn-primary' type='submit' name='_method' value='_exec'>Generate Report</button>
        </div>
      </fieldset>
    </form>    

  </div>


  <div class='span3'>
    ${show_queries(queries)}
  </div>

</div>

