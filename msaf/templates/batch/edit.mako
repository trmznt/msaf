<%inherit file="rhombus:templates/base.mako" />
<%namespace file='msaf:templates/batch/widget.mako' import='edit_batch, edit_batch_js' />

<h2>Batch</h2>
<div class='row'><div class='span8'>
  ${edit_batch(batch)}
</div></div>

<%def name="jscode()">
  ${edit_batch_js(batch)}
</%def>

