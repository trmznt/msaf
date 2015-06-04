<%inherit file="rhombus:templates/base.mako" />
<%namespace file="msaf:templates/batch/widget.mako" import="show_batch" />

<h2>Batch</h2>

<div class='row'><div class='span6'>
  ${show_batch(batch)}
</div></div>

##
<%def name="jscode()">
</%def>
