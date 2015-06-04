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
    <h3>Phylogenetics Analysis</h3>
    <form method='get' class='form-horizontal'>
      <fieldset>
        <div id="_queries">
          <div id='_initial'>
            <div class='control-group'>
              <label class='control-label' for='queryset'>Query set</label>
              <div class='controls'>
                <input type='text' id='queryset' name='queryset' value='' class='span5' />
                <span class='badge badge-important' id='_remove2' onclick="$(this).parent().parent().remove(); return false;"><i class='icon-remove'></i></span>
              </div>
              <label class='control-label' for='label'>Label</label>
              <div class='controls'>
                <input type='text' id='label' name='label' value='' class='span1' />
              </div>
            </div>
          </div>
        </div>

        <div class='control-group'><div class='controls'>
        <button class='btn' type='button' id='_addquery' name='_add' value='_clicked'>Add query set</button>
        </div></div>

        ${selection('distance', 'Distance Method',
            [ ('simple_sp', 'Proportion of pair shared [1-ps]'), ('fst', 'Fst') ])}

        ${selection('treetype', 'Tree type',
            [ ('rooted', 'Rooted'), ('circular', 'Circular') ])}

        ${selection('markers', 'Select marker(s)',
            [ (x.id, x.name) for x in markersets ], multiple=True )}
        ${input_text('threshold', 'Threshold', class_span='span1')}

        <div class='form-actions'>
          <button class='btn btn-primary' type='submit' name='_method' value='_exec'>Analyse</button>
        </div>
      </fieldset>
    </form>    

  </div>


  <div class='span3'>
    ${show_queries(queries)}
  </div>

</div>
##
##
<%def name='jscode()'>

$("#_addquery").click( function() {
    $('#_initial').clone().appendTo('#_queries');
    });
$("#_remove").click( function() {
    $(this).parent().parent().remove();
    });


</%def>
