<%namespace file='rhombus:templates/common/form.mako' import='input_text, selection' />
##
## local vars: queries, marker
##
<%def name="query_fields( markers )">

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
        ${selection('sample_option', 'Sample option',
                        [   ('A', 'All samples'), ('S', 'Strict samples'),
                            ('U', 'Unique haplotypes') ], multiple=False )}

</%def>
##
##
<%def name="differentiation_fields()">
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
                ('1', 'Year'),
                ('3', 'Quarterly'),
            ] )}
        ${selection('detection_differentiation', 'Detection differentiation',
            [   ('0', 'No'),
                ('1', 'Yes')
            ] )}

</%def>
##
##
<%def name="ctrl_fields()">
        <div class="control-group">
            <label class="control-label" for="input_file">File control input</label>
            <div class="controls">
                <input type="file" class="input-xlarge" id="ctrl_file" name="ctrl_file" />
                <p class="help-block">File control should be in YAML format.</p>
            </div>
        </div>
        <div class="control-group">
            <label class='control-label' for='yaml_ctrl'>YAML</label>
            <div class='controls'>
                <textarea id='yaml_ctrl' name='yaml_ctrl' class='' rows=10></textarea>
            </div>
        </div>
</%def>
