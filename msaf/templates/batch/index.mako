<%inherit file="rhombus:templates/base.mako" />
<%namespace file="msaf:templates/batch/widget.mako" import="list_batches, list_batches_js" />

<h2>Batch</h2>

<div class='row'><div class='span8'>
  ${list_batches(batches)}
</div></div>

<%def name="jscode()">
  ${list_batches_js()}
</%def>
