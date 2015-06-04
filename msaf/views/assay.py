import logging

log = logging.getLogger(__name__)

from pyramid.response import Response
from pyramid.renderers import render_to_response
from pyramid.httpexceptions import HTTPFound

from rhombus.lib.roles import PUBLIC
from rhombus.views import roles
from rhombus.views.errors import error_page, not_authorized

#from webhelpers import paginate
#from webhelpers.html import tags as h

from sqlalchemy import or_
from msaf.models import dbsession
from msaf.models.msdb import Assay, Allele
from msaf.lib.microsatellite.wavelen2rgb import wavelen2rgb
from msaf.lib.microsatellite import peakutils
from msaf.lib.fatools import fautils

import json
from scipy.signal import decimate


@roles( PUBLIC )
def index(request):
    """ list all assays """
    pass


@roles( PUBLIC )
def view(request):

    assay_id = int(request.matchdict.get('id', -1))
    assay = Assay.get( assay_id )
    if not assay.is_authorized( request.userinstance().groups ):
        return not_authorized()

    if not assay:
        return error_page()

    return render_to_response( 'msaf:templates/assay/view.mako',
            {   'assay': assay,
                'lsp': fautils.LadderScanningParameter() },
            request = request )


@roles( PUBLIC )
def edit(request):
    
    assay_id = int(request.matchdict.get('id', -1))
    if assay_id < 0:
        return error_page()

    if assay_id == 0:
        # create a new assay
        # for now, it is forbidden 
        raise NotImplementedError()

    else:

        assay = Assay.get( assay_id )
        if not assay:
            return error_page()

        if not assay.is_authorized( request.userinstance().groups ):
            return not_authorized()

    return render_to_response( 'msaf:templates/assay/edit.mako',
                { 'assay': assay }, request = request )

@roles( PUBLIC )
def save(request):
    if not request.POST:
        return Response('error')

    obj_id = int(request.matchdict.get('id'))

    if request.POST.get('_method') == 'save':
        obj = parse_form( request.POST )

        if obj_id == 0:
            # we need to device an authorisation mechanism here
            dbsession.add( obj )
            dbsession.flush()
            db_obj = obj
        else:
            db_obj = Assay.get(obj_id)
            if not db_obj.is_authorized( request.userinstance().groups ):
                return Response('User not in group')

            db_obj.set_ladder( obj.size_standard_id )
            db_obj.update( obj )

    return HTTPFound(location=request.route_url('msaf.assay-view', id=db_obj.id))


def parse_form( d ):
    a = Assay()
    a.panel_id = d.get('msaf-assay.panel_id')
    a.size_standard_id = d.get('msaf-assay.size_standard_id')
    return a
    

def action(request):

    if request.POST:
        return action_post(request)

    return action_get(request)


def action_get(request):

    method = request.GET.get('_method', None)

    if method == 'edit_allele':
        
        allele_id = request.GET.get('id')
        allele = Allele.get(allele_id)

        return render_to_response( 'msaf:templates/allele/edit_form.mako',
            { 'allele': allele }, request = request )

    raise RuntimeError('Unknown method: %s' % method)

def action_post(request):

    
    if not request.POST:
        return error_page()

    method = request.POST.get('_method', None)

    if method == 'delete':
        assay_ids = request.POST.getall('assay-ids')

        for assay_id in assay_ids:
            assay = Assay.get( assay_id )
            if not assay:
                request.session.flash( ('error',
                    'Assay with ID [%s] does not exists anymore.' % assay_id ) )
                continue
            if not assay.is_authorized( request.userinstance().groups ):
                request.session.flash( ('error',
                    'You are not authorized to delete assay [%s]' % assay.filename ) )

            dbsession.delete( assay )
            request.session.flash(
                ('success', 'Assay [%s] has been deleted.' % assay.filename) )

        return HTTPFound( location = request.referrer or
            request.route_url('msaf.sample-view', id=assay.sample.id) )

    elif method == 'find_ladder_peaks':
        # call peaks from ladder channel, using the supplied parameters

        assay_id = request.POST.get('assay_id')
        assay = Assay.get( assay_id )

        min_height = int(request.POST.get('min_height'))
        relative_min = float(request.POST.get('relative_min'))
        relative_max = float(request.POST.get('relative_max'))

        parameter = fautils.LadderScanningParameter()
        parameter.min_height = min_height
        parameter.min_relative_ratio = relative_min
        parameter.max_relative_ratio = relative_max

        # do peak finding
        
        #ladder_peaks, z, rss = ladder.find_ladder_peaks( min_height = min_height,
        #        relative_min = relative_min, relative_max = relative_max )[0]
        #ladder.assign_ladder_peaks( ladder_peaks )
        assay.reset()
        assay.scan_ladder_peaks(parameter)

        #assay.z = z
        #assay.rss = rss

        request.session.flash(
            ('success', 'Obtaining ladder peaks.') )

        return HTTPFound( location = request.route_url( 'msaf.assay-view', id = assay.id ))


    elif method == 'estimate_z':
        assay_id = request.POST.get('assay_id')
        assay = Assay.get(assay_id)
        assay.estimate_z()
        request.session.flash( ('success', 'Z parameters have been estimated succesfully') )

        return HTTPFound( location = request.route_url( 'msaf.assay-view', id = assay.id ))

    elif method == 'find_peaks':
        # call peaks from all channels but the ladder one, and estimate the size with Z params
        assay_id = request.POST.get('assay_id')
        assay = Assay.get( assay_id )
        if assay.z is None:
            request.session.flash( ('error', 'Assay does not have Z parameters') )
            return HTTPFound( location = request.referrer or
                    request.route_url('msaf.sample-view', id=assay.sample.id) )

        assay.scan_peaks()

        request.session.flash(
            ('success', 'Successfully searching peaks for assay: %s' % assay.filename) )

        return HTTPFound( location = request.referrer or
                    request.route_url('msaf.sample-view', id=assay.sample.id) )


    elif method == 'update_allele':

        allele_id = request.POST.get('msaf.allele_id')
        allele = Allele.get( allele_id )

        p = parse_allele( request.POST )
        allele.update(p)

        # send flash message
        request.session.flash(
            ('success', 'Successfully updating allele %s for marker %s.' %
                            (str(allele.value), allele.alleleset.marker.code) ))

        return HTTPFound( location = request.route_url('msaf.assay-view',
                                        id=allele.alleleset.channel.assay.id) )


    raise RuntimeError('method: %s ' % method)


def parse_allele( d ):

    a = Allele()
    a.value = d['msaf.allele_value']
    a.size = d['msaf.allele_size']
    a.peak = d['msaf.allele_rtime']
    a.height = d['msaf.allele_height']
    a.area = d['msaf.allele_area']
    a.type_id = int(d['msaf.allele_type_id'])
    return a


@roles( PUBLIC )
def drawchannels(request):

    assay_id = request.matchdict.get('id')
    assay = Assay.get( assay_id )
    if not assay:
        return error_page()

    datasets = {}
    for c in assay.channels:
        #downsample = decimate( c.raw_data, 3 )
        downsample = c.data
        rgb = wavelen2rgb( c.wavelen, 255 )
        datasets[c.dye] = { "data": [ [x,int(downsample[x])] for x in range(len(downsample)) ],
                            "label": "%s / %s" % (c.dye, c.marker.code),
                            "color": "rgb(%d,%d,%d)" % tuple(rgb) }

    return render_to_response( 'msaf:templates/assay/drawchannels.mako',
                { 'datasets': json.dumps( datasets ) }, request = request )





