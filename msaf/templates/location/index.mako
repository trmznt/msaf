<%inherit file="rhombus:templates/base.mako" />
<%namespace file="msaf:templates/location/widget.mako" import="list_locations, list_locations_js" />

<h2>Location/Region</h2>

<div class='row'><div class='span12'>
  ${list_locations(locations)}
</div></div>

## jscode
<%def name="jscode()">
  ${list_locations_js()}
</%def>

