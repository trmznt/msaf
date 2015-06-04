## -*- coding: utf-8 -*-
% if request.is_xhr:
  ${next.body()}

  <script type="text/javascript">
    //<![CDATA[
    ${self.jscode()}
    //]]>
  </script>
% else:
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>${ title or "MSAF - Microsatellite Analysis Framework"}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="">
    <meta name="author" content="">
    <link href="/static/rhombus/bootstrap/css/bootstrap.css" rel="stylesheet">
    <link href="/static/rhombus/select2/select2.css" rel="stylesheet">
    <style>
      body {
        padding-top: 60px; /* 60px to make the container go all the way to the bottom of the topbar */
      }
      .uneditable-input, .uneditable-textarea {
        color: rgb(59,59,59);
      }
      .sample-line {
        background-color: #EEEEEE;
      }
    </style>
    <link href="/static/rhombus/bootstrap/css/bootstrap-responsive.css" rel="stylesheet">

    <!-- HTML5 shim, for IE6-8 support of HTML5 elements -->
    <!--[if lt IE 9]>
      <script src="http://html5shim.googlecode.com/svn/trunk/html5.js"></script>
    <![endif]-->
  </head>

  <body>

    <%include file="msaf:templates/custom/header.mako" />

    <div class="container">
      ${flash_msg()}
      ${next.body()}

      <hr>
      <%include file="msaf:templates/custom/footer.mako" />
    </div>

${self.scriptlinks()}

  </body>

</html>
% endif
##
##
<%def name="userlink()">
% if request.authenticated():
    <a href="#"><i class="icon-white icon-user"></i> ${request.userinstance().login}</a>
% else:
    <a href="#"><i class="icon-white icon-user"></i> Anonymous</a>
% endif
</%def>
##
##
<%def name="scriptlinks()">
    <script src="/static/rhombus/bootstrap/js/jquery-1.7.1.min.js"></script>
    <script src="/static/rhombus/bootstrap/js/bootstrap.min.js"></script>
    <script src="/static/rhombus/select2/select2.min.js"></script>
    <script src="/static/rhombus/js/jquery.ocupload-min.js"></script>
    ${self.jslink()}
    <script type="text/javascript">
        //<![CDATA[
        ${self.jscode()}
        //]]>
    </script>
</%def>
##
##
<%def name='flash_msg()'>
% if request.session.peek_flash():

  % for msg_type, msg_text in request.session.pop_flash():
   <div class="alert alert-${msg_type}">
     <a class="close" data-dismiss="alert">×</a>
     ${msg_text}
   </div>
  % endfor

% endif
</%def>

##
<%def name='jscode()'>
</%def>

##
<%def name="jslink()">
</%def>
