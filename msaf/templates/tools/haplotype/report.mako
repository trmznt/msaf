<%inherit file="rhombus:templates/base.mako" />

##
## local vars: vpath_basepca, queryset
##

<h3>Haplotype Summary Report</h3>

<div class='row'>
  <div class='span12'>
    <p>Number of samples: ${ sum( haplotype_freqs.values() )}</p>
    <p>Unique haplotype: ${unique_haplotype}</p>
    <p>Singletons: ${haplotype_freqs[0]}</p>
  </div>
  <div class='span12'>
    <img src="${vpath_plot}" />
  </div>
</div>

