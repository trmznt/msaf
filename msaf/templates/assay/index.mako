<%inherit file="rhombus:templates/base.mako" />


<h2>Assays</h2>

<form class='form-inline' method='get'>
  <input type='text' id='q' name='q' value='${request.params.get("q","")}'class='input-xlarge' placeholder='QueryText' />
  <button type='submit' cls='btn'>Filter</button>
</form>

<div class='row'>
<div class='span12'>

<!-- list assays here -->

</div>
</div>

