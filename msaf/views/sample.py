import logging

log = logging.getLogger(__name__)

from pyramid.response import Response
from pyramid.renderers import render_to_response
from pyramid.httpexceptions import HTTPFound

from msaf.models.msdb import Sample, Batch, Assay
from msaf.models import dbsession
from sqlalchemy import or_

from rhombus.lib.roles import PUBLIC
from rhombus.views import roles
from rhombus.views.errors import error_page, not_authorized

from rhombus.lib.paginate import SqlalchemyOrmPage as Page

#from webhelpers import paginate
# from webhelpers.html import tags as h

import transaction

import dateutil.parser
import json


@roles( PUBLIC )
def index(request):

    # sanity checks, only shows shared samples or samples whose group includes the user
    #q = Sample.query().filter( or_( Sample.group_id.in_( request.userinstance().groups ),
    #                            Sample.shared == True ) )

    q = Sample.query().join(Batch).filter(
            or_(Sample.shared == True, Batch.group_id.in_( request.userinstance().groups ))
        )

    # filtering
    batch_id = request.params.get('batch_id', 0)
    batch = Batch.get( batch_id )
    if batch and batch.group_id in request.userinstance().groups:
            q = q.filter( Sample.batch_id == batch_id )
    else:
        batch = None

    # if have ids
    sample_ids = request.params.getall('ids')
    if sample_ids:
        
        q = q.filter( Sample.id.in_( sample_ids ) )

    # if have querytext
    querytext = request.params.get('q','')
    if querytext:
        from msaf.lib.querycmd import parse_querycmd

        q = q.filter( Sample.id.in_( parse_querycmd( querytext ) ) )

    # sort by code
    q = q.order_by( Sample.code )

    #page_url = paginate.PageURL_WebOb(request)
    samples = Page(q,
                    page = int(request.params.get('page', 1)),
                    items_per_page=300)
                    #url=page_url )

    return render_to_response( "msaf:templates/sample/index.mako",
                                { 'samples': samples, 'batch': batch },
                                request=request )

@roles( PUBLIC )
def view(request):
    sample_id = int(request.matchdict.get('id'))
    sample = Sample.get( sample_id )
    if sample.batch.group_id not in request.userinstance().groups:
        return not_authorized()

    return render_to_response('msaf:templates/sample/view.mako',
            { 'sample': sample }, request = request )

@roles( PUBLIC )
def edit(request):
    sample_id = int(request.matchdict.get('id', -1))
    if sample_id < 0:
        return error_page('Invalid operation, try again')
    elif sample_id == 0:
        # new sample, get the batch_id
        batch_id = request.params.get('batch_id', 0)
        batch = Batch.get( batch_id )
        if not batch:
            return error_page("Batch with id: %d is not found" % batch_id )
        if batch.group_id not in request.userinstance().groups:
            return not_authorized()

        sample = Sample()
        sample.batch_id = batch.id
        sample.id = 0

    else:
        sample = Sample.get(sample_id)
        batch = sample.batch
        if sample.batch.group_id not in request.userinstance().groups:
            return not_authorized()

    return render_to_response( "msaf:templates/sample/edit.mako",
                { 'sample': sample, 'batch': batch },
                request = request )


def save(request):
    if not request.POST:
        return error_page()

    sample_id = int( request.matchdict.get('id'))
    sample = parse_form(request.POST)
    batch = Batch.get(sample.batch_id)
    if batch.group_id not in request.userinstance().groups:
        return not_authorized()
    if sample_id != sample.id:
        return error_page('Encountering inconsistency of Sample.id (%d & %d)' % (sample_id, sample.id))

    if sample.id == 0:
        # add new sample
        sample.id = None
        dbsession.add( sample )
        dbsession.flush()
        db_sample = sample
        request.session.flash( ('success', 'Sample [%s] has been added.' % db_sample.code) )

    else:
        db_sample = Sample.get(sample_id)
        db_sample.update( sample )
        request.session.flash( ('success',
            'Modification of sample [%s] has beed saved.' % db_sample.code) )

    return HTTPFound(location = request.route_url('msaf.sample-view', id=db_sample.id))


def parse_form(d, s = None):
    if s is None:
        s = Sample()
    s.batch_id = int(d.get('msaf-sample_batch_id', 0))
    s.id = int(d.get('msaf-sample_id', 0))
    s.code = d.get('msaf-sample_code')
    s.type_id = int(d.get('msaf-sample_type_id', 0))
    s.shared = True if int(d.get('msaf-sample_shared', 0)) else False
    s.collection_date = dateutil.parser.parse(d.get('msaf-sample_collection_date'), yearfirst=True).date()
    s.location_id = int(d.get('msaf-sample_location_id', 0))
    s.comments = d.get('msaf-sample_comments')
    return s

def action(request):
    
    if not request.POST:
        return error_page()

    method = request.POST.get('_method', None)

    if method == 'delete':
        sample_ids = request.POST.getall('sample-ids')

        for sample_id in sample_ids:
            sample = Sample.get( sample_id )
            if not sample:
                request.session.flash( ('error', 'Sample with ID: %d does not exist anymore' % sample_id) )
                continue

            if not sample.is_authorized( request.userinstance().groups ):
                request.session.flash( ('error',
                'You do not have the authorization to delete sample [%s]' % sample.code) )
                continue

            sample.reset_assays()
            dbsession.delete( sample )
            request.session.flash( 
                ('success', 'Sample [%s] has been deleted' % sample.code) )

        return HTTPFound( location = request.referrer or request.route_url('msaf.sample') )

    elif method == 'add-assay':
        sample_id = request.POST.get('sample_id')
        assay_file = request.POST.get('assay_file')

        with transaction.manager:
            sample = Sample.get(sample_id)
            if not sample:
                return error_page()

            data = assay_file.file.read()
            assay = Assay( filename = assay_file.filename,
                        size_standard = 'ladder-unset',
                        panel = 'panel-unset',
                        status = 'assay-uploaded',
                        rawdata = data )
            sample.assays.append( assay )
            dbsession.flush()
            assay.create_channels()
            filename = assay.filename
            code = sample.code
            assay_id = assay.id

        request.session.flash( ('success',
            'Assay [%s] has been added to sample [%s].' % ( filename, code ) ) )

        return Response(
            json.dumps( { 'url': request.route_url("msaf.assay-view", id=assay_id) } ) )

