<%inherit file="vivaxdi:templates/base.mako" />

<h2>Sample Browser</h2>

<button class='btn'>Filter</button>

<!-- data samples -->
<div class='span12'>

<div class='row'>
    <div class='row'>
        <div class='span3'>Sample Code</div>
        <div class='span6'>country / region / district</div>
    </div>
    <div class='row'>
        <div class='span1 offset1'>Marker1<br/>12,11.9<br/>13,13.2<br/></div>
        <div class='span1'>Marker2<br/>10,9.8<br/></div>
        <div class='span1'>Marker3</div>
        <div class='span1'>Marker4</div>
        <div class='span1'>Marker5</div>
        <div class='span1'>Marker6</div>
        <div class='span1'>Marker7</div>
        <div class='span1'>Marker8</div>
        <div class='span1'>Marker9</div>
        <div class='span1'>Marker10</div>
        <div class='span1'>Marker11</div>
    </div>
    <div class='row'>
        <div class='span1 offset1'>Marker12</div>
        <div class='span1'>Marker13</div>
    </div>
</div>

<div class='row'>
    <div class='row'>
        <div class='span3'>Sample Code</div>
        <div class='span6'>country / region / district</div>
    </div>
    <div class='row'>
        <div class='span1 offset1'>Marker1<br/>12,11.9<br/>13,13.2<br/></div>
        <div class='span1'>Marker2<br/>10,9.8<br/></div>
        <div class='span1'>Marker3</div>
    </div>
</div>

<div class='row'>
    <div class='row'>
        <div class='span3'>Sample Code</div>
        <div class='span6'>country / region / district</div>
    </div>
    <div class='row'>
        <div class='span1 offset1'>Marker1<br/>12,11.9<br/>13,13.2<br/></div>
        <div class='span1'>Marker2<br/>10,9.8<br/></div>
        <div class='span1'>Marker3</div>
    </div>
</div>


</div>

<!-- data samples -->

##
##
<%def name='render_sample( sample )'>
<div class='row'>
    <div class='row'>
        <div class='span3'>${sample.name}</div>
        <div class='span3'>${sample.location.render()}</div>
    </div>
</div>
</%def>
