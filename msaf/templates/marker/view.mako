<%inherit file="rhombus:templates/base.mako" />
<%namespace file="msaf:templates/marker/widget.mako" import="show_marker" />

<h3>${h.link_to('Marker', request.route_url('msaf.marker'))}: ${marker.code}</h3>

${show_marker(marker)}

##${show_result(summary)}

##
##
<%def name='show_result(summary, marker="", q="")' >
<div class='row'><div class='span4 offset1'>
<table class='table table-condensed'>
<thead>
<tr><th>Summary</th><th>Value</th></tr>
</thead>
<tbody>
<tr><td>Samples assayed</td><td>${summary['samples_count']}</td></tr>
<tr><td>Samples with allele</td><td>${summary['samples_allele_count']}</td></tr>
<tr><td>Unique allele</td><td>${len(summary['alleles'])}</td></tr>
<tr><td>Total alleles</td><td>${summary['total_alleles']}</td></tr>
<tr><td>Heterozygosity</td><td>${'%1.3f' % summary['He']}</td></tr>
</tbody>
</table>
</div></div>

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
% for (a,s) in zip(summary['alleles'], summary['delta_status']):
<tr ${"class='error'" if not s else '' | n}><td>${a[0]}</td>
    <td class='text-right'>${'%5.3f' % a[1]}</td>
    <td class='text-right'>${h.link_to(a[2],request.route_url('msaf.sample',
        _query = { 'q': '%3.1f[allele]%s[marker]' % (a[0], marker) }))}</td>
    <td class='text-right'>${'%5.3f' % a[3]}</td>
    <td class='text-right'>${'%4.2f - %4.2f' % (a[4], a[5])}</td>
    <td class='text-right'>${'%1.2f' % a[6]}</td></tr>
% endfor
</tbody>
</table>
</div></div>
</%def>
