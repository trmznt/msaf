import logging

log = logging.getLogger(__name__)

from pyramid.response import Response
from pyramid.renderers import render_to_response
from pyramid.httpexceptions import HTTPFound

from msaf.models import dbsession
from msaf.models.msdb import Location, EK
from rhombus.lib.roles import PUBLIC, SYSADM
from msaf.lib.roles import DATAADM, LOCATION_CREATE, LOCATION_MODIFY, LOCATION_DELETE
from rhombus.views import roles

from rhombus.lib.paginate import SqlalchemyOrmPage as Page


@roles( PUBLIC )
def index(request):

    q = Location.query()

    #page_url = paginate.PageURL_WebOb(request)
    locations = Page(q,
                page = int(request.params.get('page', 1)),
                items_per_page=50)
                            #url=page_url )

    return render_to_response( "msaf:templates/location/index.mako",
                                { 'locations': locations },
                                request=request )


@roles( PUBLIC )
def view(request):

    location_id = int(request.matchdict.get('id', -1))
    location = Location.get( location_id )

    if location is None:
        return error_page()

    return render_to_response( "msaf:templates/location/view.mako",
                { 'location': location }, request=request )


@roles( PUBLIC )
def edit(request):
    location_id = int(request.matchdict.get('id', -1))
    if location_id < 0:
        return error_page('Invalid operation, try again')
    elif location_id == 0:
        # new location
        location = Location( id = 0, country_id=0,
                level1_id=0, level2_id=0, level3_id=0, level4_id=0 )
    else:
        location = Location.get( location_id )

    return render_to_response( "msaf:templates/location/edit.mako",
        { 'location': location }, request = request )


@roles( PUBLIC )
def save(request):
    location_id = int(request.matchdict.get('id', -1))

    if location_id < 0:
        return error_page()

    country = request.params.get('country','')
    level1 = request.params.get('level1','')
    level2 = request.params.get('level2','')
    level3 = request.params.get('level3','')
    level4 = request.params.get('level4', '')
    latitude = request.params.get('latitude','')
    longitude = request.params.get('longitude')
    
    if location_id == 0:
        location = Location.search( country, level1, level2, level3, level4, True )
    else:
        location = Location.get( location_id )
        # TODO
        # need to check whether current user is authorized to edit this Location instance
        # by checking lastuser_id is in group with current_user_id
        country_id = EK._id(country, '@REGION', auto)
        level1_id = EK._id(level1, '@REGION', auto)
        level2_id = EK._id(level2, '@REGION', auto)
        level3_id = EK._id(level3, '@REGION', auto)
        level4_id = EK._id(level4, '@REGION', auto)
        location.country_id = country_id
        location.level1_id = level1_id
        location.level2_id = level2_id
        location.level3_id = level3_id
        location.level4_id = level4_id

    if latitude:
        location.latitude = float(latitude)
    if longitude:
        location.longitude = float(longitude)

    return HTTPFound(location='/location')


@roles( PUBLIC )
def save(request):
    if not request.POST:
        return error_page()

    location_id = int( request.matchdict.get('id') )
    location = parse_form( request.POST )

    if location_id != location.id:
        return error_page('Encountering inconsistency')

    if location.id == 0:
        # add new location
        location.id = None
        dbsession.add( location )
        dbsession.flush()
        db_location = location
        request.session.flash( ('success', 'Location %s has been added' % db_location.render()) )

    else:
        db_location = Location.get( location_id )
        db_location.update( location )

    return HTTPFound(location='/location')


@roles( PUBLIC )
def lookup(request):
    """ return JSON for autocomplete """
    q = request.params.get('q')
    field = request.params.get('field', None)

    q = q.strip()
    if not q:   
        return error_page()

    if field:
        regions = EK.get_members('@REGION').filter( EK.key.contains(q.lower()) )
        region_names = [ r.key for r in regions ]
        region_names.sort()

        # return suitable for bootstrap typeahead
        return region_names

    locations = Location.grep( q )

    # return suitable for select2 js component
    location_data = [ { 'id': l.id, 'text': l.render()} for l in locations ]
    return location_data


def parse_form(d):
    auto = True
    l = Location()
    l.id = int(d.get('msaf-location_id', 0))
    l.country_id = EK._id(d.get('msaf-country'), '@REGION', auto)
    l.level1_id = EK._id(d.get('msaf-adminl1'), '@REGION', auto)
    l.level2_id = EK._id(d.get('msaf-adminl2'), '@REGION', auto)
    l.level3_id = EK._id(d.get('msaf-adminl3'), '@REGION', auto)
    l.level4_id = EK._id(d.get('msaf-adminl4'), '@REGION', auto)
    l.latitude = float(d.get('msaf-latitude') or 0)
    l.longitude = float(d.get('msaf-longitude') or 0)
    l.altitude = float(d.get('msaf-altitude') or 0)

    return l

@roles( SYSADM, DATAADM, LOCATION_MODIFY, LOCATION_DELETE )
def action(request):

    if not request.POST:
        return error_page()

    method = request.POST.get('_method')

    if method == 'delete':
        ids = request.POST.getall('location-ids')
        locations = list( Location.query().filter( Location.id.in_( ids ) ) )

        if len(locations) == 0:
            return Response(modal_error)

        return Response(modal_delete % ''.join( '<li>%s</li>' % x.render() for x in locations ))

    elif method == 'delete/confirm':
        ids = request.POST.getall('location-ids')

        c = 0
        for location_id in ids:
            Location.delete( location_id )
            c += 1

        request.session.flash( ('success', 'Removing %d location(s)' % c) )

        return HTTPFound(location = request.referer)


modal_delete = '''
<div class="modal-header">
    <button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>
    <h3 id="myModalLabel">Deleting Location</h3>
</div>
<div class="modal-body">
    <p>You are going to delete the following location(s):
        <ul>
        %s
        </ul>
    </p>
</div>
<div class="modal-footer">
    <button class="btn" data-dismiss="modal" aria-hidden="true">Cancel</button>
    <button class="btn btn-danger" type="submit" name="_method" value="delete/confirm">Confirm Delete</button>
</div>
'''

modal_error = '''
<div class="modal-header">
    <button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>
    <h3 id="myModalLabel">Error</h3>
</div>
<div class="modal-body">
    <p>Please select location(s) to be removed</p>
</div>
<div class="modal-footer">
    <button class="btn" data-dismiss="modal" aria-hidden="true">Close</button>
</div>
'''




