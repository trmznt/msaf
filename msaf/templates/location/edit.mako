<%inherit file="rhombus:templates/base.mako" />
<%namespace file='msaf:templates/location/widget.mako' import='edit_location, edit_location_js' />

<h2>Location/Region</h2>
<div class='row'><div class='span8'>
  ${edit_location(location)}
</div></div>

##
##
<%def name="jscode()">
  ${edit_location_js(location)}
</%def>
