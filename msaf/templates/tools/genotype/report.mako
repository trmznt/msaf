<%inherit file='rhombus:templates/base.mako' />

##
## local vars: reports, csvfile
##

<h2>Genotype Summary Report</h2>

<div class='row'>

<p>Tab-delimited genotype file: ${h.link_to('here', tabfile)}</p>
</div>

% for (label, data, aux_data, assay_data) in reports:
  <div class='row'><div class='span12'>
    <h3>Dataset: ${label}</h3>

    <table class='table table-condensed'>
    <thead>
      <tr><th>${'</th><th>'.join( data[0] ) | n}</th></tr>
    </thead>
    <tbody>
    % for row,aux_row,assay_row in zip(data[1:], aux_data[1:], assay_data[1:]):
      <tr><td>${h.link_to(row[0][0], request.route_url('msaf.sample-view', id=row[0][1])) if row[0] else ''}</td><td>${'</td><td>'.join( 
      [ '<a href="/assay/%s"><span class="%s">%s</label></a>' % 
        ( a, ('text-green' if y > 25 else 'text-red') if y else '', str(x) ) for x,y,a in zip(row[1:], aux_row[1:], assay_row[1:]) ] ) | n}</td></tr>
    % endfor
    </tbody>
    </table>
  </div></div>
% endfor

