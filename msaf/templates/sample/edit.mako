<%inherit file="rhombus:templates/base.mako" />
<%namespace file="msaf:templates/sample/widget.mako" import="edit_sample, edit_sample_js" />

<h2>Sample Editor</h2>

<div class='row'><div class='span8'>
  ${edit_sample(sample, batch)}
</div></div>

<%def name="jscode()">
  ${edit_sample_js(sample)}
</%def>
