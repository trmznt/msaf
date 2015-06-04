##
##
<%def name="show_queries(queries, length=10)">
% for queryset in queries[:length]:
  <div><span class='label label-info'>&#35;${queryset.id}</span> (${queryset.count})<br/>
    ${queryset.query_text}
  </div>
% endfor
</%def>
##
