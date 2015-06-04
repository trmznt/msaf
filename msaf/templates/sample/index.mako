<%inherit file="rhombus:templates/base.mako" />
<%namespace file="msaf:templates/sample/widget.mako" import="list_samples, list_samples_js" />

<h2>Samples</h2>

<form class='form-inline' method='get'>
  <input type='text' id='q' name='q' value='${request.params.get("q","")}'class='input-xlarge' placeholder='QueryText' />
  <button type='submit' cls='btn'>Filter</button>
</form>

% if batch is not None:
  <!-- show Batch information -->
  <div class='row'>
    <div class='span2'>
      <a class='btn btn-small btn-success pull-right' href='${request.route_url("msaf.sample-edit", id=0, _query = {"batch_id": batch.id})}'>Add New sample</a>
    </div>
    <div class='span4'><p>Batch code:
    <a href="${request.route_url('msaf.batch-view', id=batch.id)}">${batch.code}</a></p></div>
  </div>
% endif

<div class='row'><div class='span12'>
% if request.params.get('sampleview') == 'detailed':
  <!-- show samples in detailed view -->
% elif request.params.get('sampleview') == 'condensed':
  <!-- show samples in condensed view -->
% else:
  <!-- show samples in standard, simple view -->
  ${list_samples(samples)}
% endif
</div></div>
##
##
<%def name="jscode()">
  ${list_samples_js()}
</%def>




