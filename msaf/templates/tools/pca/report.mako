<%inherit file="rhombus:templates/base.mako" />

##
## local vars: vpath_basepca, queryset
##

<h3>PCA (Principal Component Analysis) Result</h3>

<div class='row'>
  <div class='span12'>
    % for vpath_basepca in  vpaths_basepca:
      <img src='${vpath_basepca}' />
    % endfor
  </div>
</div>

