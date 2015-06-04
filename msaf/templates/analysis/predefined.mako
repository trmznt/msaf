<%inherit file='vivaxdi:templates/base.mako' />
<%namespace file='vivaxdi:templates/queryset/common.mako'
  import='show_queries' />
<%namespace file='vivaxdi:templates/commonforms.mako'
  import='input_text, selection' />
##
## local vars: queries, markersets
##
<div class='row'>

  <div class='span9'>
    <h3>Predefined Analysis</h3>

    <ul>
    <li>All Indonesian samples with MS10, msp1f3, msp3alpha, msp4, msp5, pv3.27 (threshold:100)</li>
    <ul>
        <li><a href="http://localhost:7654/analysis/allele?queryset=indonesia[country]&markers=3&markers=7&markers=10&markers=8&markers=9&markers=1&threshold=100&_method=_exec">Allele Summary</a></li>
        <li><a href="http://localhost:7654/analysis/allele?queryset=indonesia[country]&markers=3&markers=7&markers=10&markers=8&markers=9&markers=1&threshold=100&_method=_exec">MoI</a></li>
    </ul>
    </ul>

  </div>
</div>
