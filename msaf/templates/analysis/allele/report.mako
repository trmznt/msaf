<%inherit file="rhombus:templates/base.mako" />

<%namespace file='msaf:templates/marker/view.mako'
  import='show_result' />
##
## local vars: results, queryset
##
<h3>Allele Summary Report</h3>

<table class='table table-condensed'>
<tbody>
<tr><td>Sample query</td><td>${queryset}</td></tr>
<tr><td>Sample size</td><td>${sample_size}</td></tr>
<tr><td>Threshold</td><td>${threshold}</td></tr>
<tr><td>Average He</td><td>${'%1.3f' % He}</td></tr>
</tbody>
</table>

<h4>Summary</h4>
<table class='table table-condensed'>
<thead>
<tr><th>Marker</th><th>Sample assayed</th><th>Samples with allele</th>
    <th>Unique allele</th><th>Total alleles</th><th>Heterozygosity</th></tr>
</thead>
<tbody>
% for res in results:
<tr><td>${res['marker']}</td><td>${res['samples_count']}</td>
    <td>${res['samples_allele_count']}</td><td>${len(res['alleles'])}</td>
    <td>${res['total_alleles']}</td><td>${'%2.3f' % res['He']}</td></tr>
% endfor
</tbody>
</table>

% for res in results:
<h4>${res['marker']}</h4>
${show_result( res, marker=res['marker'] )}
% endfor

