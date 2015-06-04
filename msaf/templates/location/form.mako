<%namespace file='msaf:templates/commonforms.mako' import='input_text, submit_bar' />
##
##
<%def name="location_form(location)">
<form class='form-horizontal' method='post'
    action='${request.route_url("vivaxdi.location-save", id=location.id)}'>
  <fieldset>
    ${input_text('country', 'Country', value = location.country or '')}
    ${input_text('state', 'State', value = location.state or '')}
    ${input_text('region', 'Region', value = location.region or '')}
    ${input_text('town', 'Town', value = location.town or '')}
    ${input_text('latitude', 'Latitude', value = location.latitude or '')}
    ${input_text('longitude', 'Longitude', value = location.longitude or '')}
    ${submit_bar()}
  </fieldset>
</form>
</%def>
##
##
<%def name="js_location_form()">
    $.each( ['#country', '#state', '#region', '#town'], function(idx, val) {
    $(val).typeahead( {
        source: function( query, process ){
            return $.get("${request.route_url('msaf.location-lookup')}", { q: query, field: 1 }, function(data) {
                return process(data);
            });
        },
        minLength: 3
    });
  })
</%def>
