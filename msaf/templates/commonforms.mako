##
##
<%def name="input_text(name, label, class_='control-group', class_span = '', value='')">
<div class='${class_}'>
  <label class='control-label' for='${name}'>${label}</label>
  <div class='controls'>
    <input type='text' id='${name}' name='${name}' value='${value}' ${"class='%s'" % class_ if class_.startswith('span') else "class='%s'" % class_span | n} />
  </div>
</div>
</%def>
##
##
<%def name="input_textarea(name, label, class_='control-group', class_span='', value='')">
<div class='${class_}'>
  <label class='control-label' for='${name}'>${label}</label>
  <div class='controls'>
    <textarea id='${name}' name='${name}' class='${class_span}'>${value}</textarea>
  </div>
</div>
</%def>
##
##
<%def name="selection(name, label, params, class_='control-group', class_span='', value='', multiple=False)">
<div class='${class_}'>
  <label class='control-label' for='${name}'>${label}</label>
  <div class='controls'>
    <select id='${name}' name='${name}' class='${class_span}' ${'multiple="multiple"' if multiple else '' | n}>
    % for (key, val) in params:
      % if value and value == key:
        <option value='${key}' selected='selected'>${val}</option>
      % else:
        <option value='${key}'>${val}</option>
      % endif
    % endfor
    </select>
  </div>
</div>
</%def>
##
##
<%def name="checkboxes( name, label, params, class_='control-group', class_span='')">
<div class="${class_}">
  <label class="control-label" for="${name}">${label}</label>
  % for (n, l, v, c) in params:
  <div class="controls">
    <label class="checkbox">
      <input id="${name}" type="checkbox" name="${n}" value="${v}" ${"checked='checked'" if c else ''} />
      ${l}
    </label>
  </div>
  % endfor
</div>
</%def>
##
##
<%def name="selection_ck( name, label, ck_group, class_='control-group', class_span='', value='')">
${selection( name, label,
        [ (k.id, k.key) for k in request.CK().get_members(ck_group) ],
        value = value )}
</%def>
##
##
<%def name="submit_bar( name='Save', value='save')">
  <div class='form-actions'>
    <button class='btn btn-primary' type='submit' name='_method' value='${value}'>${name}</button>
    <button class='btn' type='reset'>Reset</button>
  </div>
</%def>
##
##
<%def name="input_hidden( name, label, class_='control-group', class_span='', value='')">
<div class='${class_}'>
  % if label:
  <label class='control-label' for='${name}'>${label}</label>
  % endif
  <div class='controls'>
    <input type='hidden' id='${name}' name='${name}' value='${value}' ${"class='%s'" % class_ if class_.startswith('span') else "class='%s'" % class_span | n} />
  </div>
</div>

</%def>
##
##
<%def name="input_ck( name, label, url, class_='control-group', class_span='', value='')">
<div class='${class_}'>
  <label class='control-label' for='${name}'>${label}</label>
  <div class='controls'>
    <input type='text' id='${name}' name='${name}' value='${value}'
      ${"class='%s'" % class_ if class_.startswith('span') else "class='%s'" % class_span | n}
      data-provide="typeahead"
      data-source="function( query, process ){ return $.get('${url}', { q: query }, function(data) { return process(data);});}"
      />
  </div>
</div>
</%def>
