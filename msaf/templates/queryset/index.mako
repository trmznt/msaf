<%inherit file="rhombus:templates/base.mako" />

<div class='row'>
  <div class='span9'>
    <h2>Query Wizard</h2>
    <form method='post'>
      <fieldset>
        <div class='control-group'>
          <label class='control-label' for='desc'>Description (optional)</label>
          <input type='text' id='desc' name='desc' value='' class='span8' />
        </div>
      </fieldset>
      <fieldset>
        <div class='control-group'>
          <div class='span1'>
            <label class='control-label' for='query_text'><b>Query Text</b></label>
          </div>
          <textarea name='query_text' id='query_text' class='span7'></textarea>
        </div>
        <div class='span8'>
          <div class='form-actions'>
            <button class='btn btn-primary' type='submit' name='_method' value='_querytext'>
            Query Text Search
            </button>
            <button class='btn btn-primary' type='submit' name='_method' value='_querytest'>
            Test Query
            </button>
            <button class="btn" type='reset'>Reset</button>
          </div>
        </div>
      </fieldset>
      <fieldset>
        <div class='control-group'>
          <div class='span1'>
            <label class='control-label'><b>Query Form</b></label>
          </div>
          <div class='span7'>
            <!-- rows -->
            <div class='row'>
              ${input_text('location', 'Location: (country/state/region/town)', 'span4')}
              ${input_text('collection_date', 'Collection date: (year/month/date)', 'span3')}
            </div>
            <div class='row'>
              ${input_text('age', 'Age', 'span1')}
              ${input_text('gender', 'Gender', 'span1')}
              ${input_text('microscopic_ident', 'Microscopic identification', 'span2')}
              ${input_text('pcr_ident', 'PCR identification', 'span2')}
            </div>
            <div class='row'>
              ${input_text('marker_name', 'Marker name', 'span2')}
              ${input_text('allele_count', 'Allele count', 'span1')}
              ${input_text('allele_size', 'Allele size', 'span2')}
              ${input_text('allele_height', 'Allele height', 'span2')}
            </div>
          </div>
        </div>
        <div class='span8'>
          <div class='form-actions'>
            <button class='btn btn-primary' type='submit' name='_method' value='_querytext'>
            Query Form Search
            </button>
            <button class="btn" type='reset'>Reset</button>
          </div>
        </div>
      </fieldset>

    </form>
  </div>
  <div class='span3'>
    <div class="accordion" id="accordion2">

      <div class="accordion-group">
        <div class="accordion-heading">
          <a class="accordion-toggle" data-toggle="collapse" data-parent="#accordion2" href="#collapseOne">Saved queries</a>
        </div>
        <div id="collapseOne" class="accordion-body collapse in">
          <div class="accordion-inner">
            ${show_queries()}
          </div>
        </div>
      </div>

      <div class="accordion-group">
        <div class="accordion-heading">
          <a class="accordion-toggle" data-toggle="collapse" data-parent="#accordion2" href="#collapseTwo">Documentation/Help</a>
        </div>
        <div id="collapseTwo" class="accordion-body collapse">
          <div class="accordion-inner" style="overflow: auto; max-height: 500px;">
            ${show_help()}
          </div>
        </div>
      </div>

    </div>
  </div>
</div>

##
##
<%def name="input_text(name, label, class_span, value='')">
<div class='${class_span}'>
  <label class='control-label'>${label}</label>
  <input type='text' id='${name}' name='${name}' value='${value}' class='${class_span}' />
</div>
</%def>
##
##
<%def name="show_queries(length=10)">
% for queryset in queries[:length]:
  <div><span class='label label-info'>&#35;${queryset.id}</span> (${queryset.count})<br/>
    ${queryset.query_text}
  </div>
% endfor
</%def>
##
##
<%def name="show_help()">
${docs|n}
</%def>
