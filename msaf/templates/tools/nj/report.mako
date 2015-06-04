<%inherit file="rhombus:templates/base.mako" />

##
## local vars: vpath_nj, queryset
##

<h3>NJ (Neighbor Joining) Tree Result</h3>

<div class='row'>
  <div class='span12'>
    % if vpath_nj:
      <img src='${vpath_nj}' />
    % endif
    % if vpath_nj_pdf:
      <p>${h.link_to('PDF image', vpath_nj_pdf)}</p>
    % endif
  </div>
</div>

