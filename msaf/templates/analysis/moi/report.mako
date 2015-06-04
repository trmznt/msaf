<%inherit file="rhombus:templates/base.mako" />

##
## local vars: result, queryset, threshold
##
<h3>Multiplicity of Infection (MoI) Report</h3>

<table class='table table-condensed'>
<tbody>
<tr><td>Sample query</td><td>${queryset}</td></tr>
<tr><td>Sample size</td><td>${result['sample_size']}</td></tr>
<tr><td>Threshold</td><td>${threshold}</td></tr>
<tr><td>Mean MoI</td><td>${result['mean']}</td></tr>
<tr><td>Median MoI</td><td>${result['median']}</td></tr>
</tbody>
</table>

<div class='row'>
  <div class='span3 offset1'>
    <table class='table table-condensed'>
      <thead>
        <tr><th>No of loci with > 1 allele</th><th>Sample Frequency</th></tr>
      </thead>
      <tbody>
        % for i in range(1, len(result['loci_distribution'])):
          <tr><td>${i}</td><td>${result['loci_distribution'][i]}</td></tr>
        % endfor
      </tbody>
    </table>
  </div>
  <div class='span3 offset1'>
    <table class='table table-condensed'>
      <thead>
        <tr><th>MoI</th><th>Sample Frequency</th></tr>
      </thead>
      <tbody>
        % for i in sorted( result['moi_distribution'].keys() ):
          <tr><td>${i}</td><td>${result['moi_distribution'][i]}</td></tr>
        % endfor
      </tbody>
    </table>
  </div>
</div>



