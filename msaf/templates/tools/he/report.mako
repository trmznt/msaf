<%inherit file='rhombus:templates/base.mako' />

##
## local vars: reports, csvfile
##

<h2>Expected Heterozygosity</h2>

<div class='row'>
</div>


<div class='row'><div class='span12'>

  <table class='table table-condensed'>
    <thead>
      <tr><th>${'</th><th>'.join( table[0] ) | n}</th></tr>
    </thead>
    <tbody>
    % for row in table[1:]:
      <tr><td>${row[0]}</td><td>${'</td><td>'.join( [ "%4.3f" % x if type(x) is not str else "" for x in row[1:] ] ) | n}</td></tr>
    % endfor
    </tbody>
  </table>

  % if 'stats' in reports:
  <p>p-value = ${"%4.3f" % reports['stats'][1]}</p>
  <p>Statistic test = ${reports['test']}</p>
  % endif

</div></div>

