import logging

log = logging.getLogger(__name__)

from pyramid.response import Response
from pyramid.renderers import render_to_response
from pyramid.httpexceptions import HTTPFound
from msaf.models.msdb import Sample, Batch
from msaf.models import dbsession
from rhombus.lib.roles import PUBLIC
from rhombus.views import roles
from rhombus.lib.paginate import SqlalchemyOrmPage as Page
import transaction

#from webhelpers import paginate

@roles( PUBLIC )
def index(request):

    q = Batch.query().filter( Batch.group_id.in_( request.userinstance().groups ) )

    #page_url = paginate.PageURL_WebOb( request )
    batches = Page( q,
                page = int(request.params.get('page', 1)),
                items_per_page = 30)
    #            url = page_url )

    return render_to_response( "msaf:templates/batch/index.mako",
            { 'batches': batches },
            request = request )

def add(request):
    pass

def view(request):
    batch_id = int(request.matchdict.get('id', -1))
    batch = Batch.get(batch_id)
    if not batch:
        return error_page('Batch not found')

    return render_to_response( "msaf:templates/batch/view.mako",
            { 'batch': batch }, request = request )

def edit(request):
    batch_id = int(request.matchdict.get('id', -1))
    if batch_id < 0:
        return error_page( 'Invalid operation. Please try again.' )
    if batch_id == 0:
        # new batch
        batch = Batch()
        batch.id = 0
    else:
        batch = Batch.get( batch_id )
    return render_to_response( "msaf:templates/batch/edit.mako",
            { 'batch': batch }, request = request )

@roles( PUBLIC )
def save(request):
    if not request.POST:
        return Response('error')

    batch_id = int(request.matchdict.get('id'))

    if request.POST.get('_method') == 'save':
        batch = parse_form( request.POST )
        if batch.group_id not in request.userinstance().groups:
            return Response('User not in group')

        if batch_id == 0:
            dbsession.add( batch )
        else:
            db_batch = Batch.get(batch_id)
            db_batch.update(batch)

    return HTTPFound(location='/batch')

def parse_form(d):
    """ return an instance from dictionary d """
    batch = Batch()
    batch.code = d.get('msaf-batch_code')
    batch.desc = d.get('msaf-batch_desc')
    batch.group_id = int(d.get('msaf-batch_group_id'))
    batch.assay_provider_id = int(d.get('msaf-assay_provider_id'))
    return batch

def action(request):
    
    if not request.POST:
        return error_page()

    method = request.POST.get('_method', None)

    if method == 'delete':
        batch_ids = request.POST.getall('batch-ids')
        batches = list( Batch.query().filter( Batch.id.in_( batch_ids ) ) )

        if len(batches) == 0:
            return Response(modal_error)

        return Response(modal_delete % ''.join( '<li>%s</li>' % b.code for b in batches ))


    if method == 'delete/confirm':
        batch_ids = request.POST.getall('batch-ids')

        for batch_id in batch_ids:
            batch = Batch.get( batch_id )
            if not batch:
                request.session.flash( ('error',
                    'Batch with ID [%d] does not exists' % batch_id) )
                continue
            if not batch.is_authorized( request.userinstance().groups ):
                request.session.flash( ('error',
                    'You are not authorized to delete batch [%s]' % batch.code) )

            code = batch.code
            batch.reset_samples()
            dbsession.delete( batch )
            request.session.flash(
                ('success', 'Batch [%s] has been deleted' % code ) )


        return HTTPFound( location = request.referrer or 
            request.route_url( 'msaf.batch' ) )

    raise RuntimeError('Unknown method')
        
def lookup(request):
    pass


modal_delete = '''
<div class="modal-header">
    <button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button>
    <h3 id="myModalLabel">Deleting Batch(es)</h3>
</div>
<div class="modal-body">
    <p>You are going to delete the following Batch(es):
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
    <p>Please select Batch(es) to be removed</p>
</div>
<div class="modal-footer">
    <button class="btn" data-dismiss="modal" aria-hidden="true">Close</button>
</div>
'''

