<%inherit file="rhombus:templates/base.mako" />
<%namespace file="msaf:templates/marker/widget.mako" import="list_markers, list_markers_js" />

<h2>Markers</h2>

<div class="row"><div class="span12">
  ${list_markers(markers)}
</div></div>

##
##
<%def name="jscode()">
  ${list_markers_js()}
</%def>

