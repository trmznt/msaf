<%inherit file="rhombus:templates/base.mako" />
<%namespace file="msaf:templates/sample/widget.mako" import="show_sample, show_sample_js" />
<%namespace file="msaf:templates/assay/widget.mako" import="list_assays, list_assays_js" />
<%namespace file="msaf:templates/allele/widget.mako" import="list_alleles_column" />

## params: sample, allele_list
##

<h2>Sample Viewer</h2>

${show_sample(sample)}

<h3>Alleles</h3>
${list_alleles_column(allele_list)}

<h3>Assays</h3>
${list_assays(sample.assays)}

##
##
<%def name="jscode()">
  ${show_sample_js(sample)}
  ${list_assays_js(sample)}
</%def>

