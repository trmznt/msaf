<%inherit file="rhombus:templates/base.mako" />
<%namespace file="msaf:templates/marker/widget.mako" import="edit_marker" />

<h3>${h.link_to('Marker', request.route_url('msaf.marker'))}: ${marker.code}</h3>

${edit_marker(marker)}


