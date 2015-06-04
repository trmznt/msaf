<%inherit file="rhombus:templates/base.mako" />
<%namespace file="msaf:templates/assay/widget.mako" import="edit_assay, edit_assay_js" />

<h2>Assay Editor</h2>

<div class='row'><div class='span8'>
  ${edit_assay(assay, sample)}
</div></div>

<%def name="jscode()">
  ${edit_assay_js(sample)}
</%def>
