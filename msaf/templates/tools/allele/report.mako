<%inherit file="rhombus:templates/base.mako" />

##
## local vars: results, ploturl
##

<h3>Allele Calling Summary Report</h3>

<div class='row'>


</div>

% for label in results:

  <h3>${label}</h3>

  % for r in results[label].values():
    <div class='row'><div class='span12'>
      <h3>${r['code']}</h3>
      <p>Unique allele = ${r['unique_allele']}</p>
      <p>Total allele = ${r['total_allele']}</p>
    </div></div>

    ${show_alleles(r['alleles'], r['delta_status'])}

  % endfor

% endfor

% if ploturl:
<div class='row'>
PDF plot file: ${h.link_to('file', ploturl)}
</div>
% endif


##
##

<%def name="show_alleles(alleles, delta_status)">

<div class='row'><div class='span8 offset2'>
<table class='table table-condensed'>
<thead>
<tr><th>Value</th>
    <th class='text-right'>f</th>
    <th class='text-right'>n</th>
    <th class='text-right'>Avg Height</th>
    <th class='text-right'>Size range</th>
    <th class='text-right'>D range</th></tr>
</thead>
<tbody>
% for (a,s) in zip(alleles, delta_status):
  <tr ${"class='error'" if not s else '' | n}>
    <td>${a[0]}</td>
    <td class='text-right'>${'%5.3f' % a[1]}</td>
    <td class='text-right'>${h.link_to(a[2],request.route_url('msaf.sample',
        _query = [ ('ids', x) for x in a[7]]  ))}</td>
    <td class='text-right'>${'%5.3f' % a[3]}</td>
    <td class='text-right'>${'%4.2f - %4.2f' % (a[4], a[5])}</td>
    <td class='text-right'>${'%1.2f' % a[6]}</td>
  </tr>
% endfor
</tbody>
</table>
</div></div>

</%def>
