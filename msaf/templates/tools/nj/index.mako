<%inherit file="rhombus:templates/base.mako" />
<%namespace file='msaf:templates/queryset/common.mako'
  import='show_queries' />
<%namespace file='rhombus:templates/common/form.mako'
  import='input_text, selection, input_file, submit_bar' />
<%namespace file='msaf:templates/tools/queryforms.mako'
  import='query_fields, differentiation_fields' />


<div class='row'>

  <div class='span9'>
    <h3>NJ - Neighbor Joining Tree</h3>
    <form method='post' class='form-horizontal' enctype="multipart/form-data">
      <fieldset>
        ${query_fields(markers)}
        ${differentiation_fields()}
        ${input_file('labelfile', 'Label modifier file')}
        <!-- Need to create JS to change method to GET when labelfile is empty -->

        ${submit_bar('Generate NJ Tree', '_exec')}
      </fieldset>
    </form>
  </div>


  <div class='span3'>
    ${show_queries(queries)}
  </div>

</div>


