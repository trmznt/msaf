<%inherit file="rhombus:templates/base.mako" />

##
## local vars: infile, paramfile
##

<h3>STRUCTURE File Exporter</h3>

<div class='row'>
  <div class='span12'>
    % if infile and paramfile:
        <p>STRUCTURE input file: ${h.link_to( 'infile', infile)}</p>
        <p>STRUCTURE param file: ${h.link_to( 'paramfile', paramfile)}</p>
    % endif
  </div>
</div>

