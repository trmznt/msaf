<%inherit file="rhombus:templates/base.mako" />

##
## local vars: result, queryset, threshold
##

<h3>LIAN 3.5 Result</h3>

<div class='row'>
  <div class='span4'>
    <table class='table table-condensed'>
    <tr><td class='text-right'>LD :</td><td>${result.get_LD()}</td></tr>
    <tr><td class='text-right'>p-value :</td><td>${result.get_pvalue()}</td></tr>
    </table>
  </div>
</div>

<pre>
${result.get_output().replace('\n', '<br />') | n}
</pre>

