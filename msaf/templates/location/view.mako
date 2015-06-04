<%inherit file="rhombus:templates/base.mako" />
<%namespace file='msaf:templates/location/widget.mako' import='show_location' />

<h2>Location</h2>

${show_location(location)}
