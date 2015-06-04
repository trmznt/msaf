<%inherit file="rhombus:templates/base.mako" />

##
## local vars: figures
##

<h3>MoI Result</h3>

<div class='row'>
  % for fig in figures:
  <div class='span12'>
      <img src='${fig}' />
  </div>
  % endfor
</div>

