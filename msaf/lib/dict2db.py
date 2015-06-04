
from msaf.models import *
from io import StringIO
from datetime import date


dye_color = dict( B = '6-FAM', G = 'VIC', Y = 'NED', O = 'LIZ', R = 'PET' )


def boolean(text):
    # if text is already None, return False
    if not text:
        return False

    # if text is a string, check the first letter
    if type(text) == str:
        if text[0] in 'Yy':
            return True
        else:
            return False

    # otherwise, just check the text itself
    return True if text else False


def species(text):
    if not text:
        return 'X'
    if '/' in text:
        species = [ x.strip() for x in text.split('/') ]
        return '/'.join( sorted( species ) )
    return text


class Sample_CtxMgr(object):

    def __init__(self, sample_code, data):
        pass
    def pre(self):
        pass
    def post(self, sample):
        pass


def dict2sample( sample_code, data, group_id, batch, auto=True, update_only = False,
                    sample_class = Sample, sample_ctxmgr = Sample_CtxMgr ):
    """ given the dict in data, return the sample """

    print("Creating a new sample with code: %s for batch: %s" % ( sample_code, batch.code ))

    collection_date = date(*[ int(x) for x in data['collection_date'].split('/') ])
    location = Location.search( *[ x.lower() for x in data['location'] ], auto=auto )

    if not location:
        raise RuntimeError('Location %s cannot be inserted to database!' %
                    str( data['location'] ))

    ctx = sample_ctxmgr( sample_code, data)
    ctx.pre()
    print(sample_class)

    sample = sample_class.search( code=sample_code,
                            batch_id = batch.id,
                            collection_date = collection_date,
                            location_id = location.id,
                            auto = auto )
    if not sample:
        raise RuntimeError('Sample %s cannot be inserted to database!' % sample_code)

    if not sample.id:
        if update_only:
            # if update_only, prevent from submiting new samples
            raise RuntimeError('Cannot update sample [%s]. No such sample in the database!'
                    % sample.code )
            
        # new sample submission, import other information
        sample.comments = data['comments'] or None
        sample.group_id = group_id
        sample.type_id = EK._id('sample-field', '@SAMPLE-TYPE')
        sample.batch = batch

        ctx.post( sample )

    return sample


def dict2update_sample( sample, data ):

    if data.get('collection_date', None):
        collection_date = date(*[ int(x) for x in data['collection_date'].split('/') ])
        sample.collection_date = collection_date

    if data.get('location', None):
        location = Location.search( *[ x.lower() for x in data['location'] ], auto=True )
        sample.location = location


def dict2assay( assay_name, data, auto=False, sample=None ):
    # XXX: need to use search instead of creating new assay
    # we assume that assay is always new

    # check for assay_provider
    assay = Assay( filename = assay_name,
                    size_standard_id = EK._id( data['size_standard'] ),
                    panel_id = Panel.search( 'external' ).id,
                    status_id = EK._id( 'assay-unavailable', '@ASSAY-STATUS'),
                    assay_provider_id = sample.batch.assay_provider_id,
                    #panel_id = EK._id( data['panel'] ),
        )
    if 'rawdata' in data:
        raise NotImplemented('rawdata needs to be decoded from base64')
        assay.rawdata = data['rawdata']
    else:
        assay.rawdata = b''
    return assay


def dict2alleleset( dye, assay, marker, auto=False ):
    # XXX: do we need to search first?

    # create channel
    channel = Channel(wavelen=-1, status_id = EK._id('channel-unavailable', '@CHANNEL-STATUS'),
            marker_id = marker.id,
            dye_id = EK._id(dye, '@DYE') if len(dye) > 1 else EK._id(dye_color[dye], '@DYE'),               raw_data = numpy.zeros(0), data = numpy.zeros(0))
    channel.assay = assay

    # create alleleset
    return AlleleSet( channel = channel, sample = assay.sample, marker_id = marker.id,
        method_id = EK._id('allele-external', '@ALLELE-METHOD') )


def dict2db( samples, batch_code='', desc='', group_id=0, assay_provider_id=0,
        update_sample = False, update_allele = False, update_info = False,
        sample_class = Sample, sample_ctxmgr = Sample_CtxMgr ):
    """ update_sample: use existing BATCH code, prevent adding existing sample_id
        update_allele: replace/add new allele for marker
    """

    if type(samples) != dict:
        raise RuntimeError('Wrong file format. Must be a map/dictionary object')

    batch =  Batch.search( code = batch_code )
    if batch and not (update_sample or update_allele or update_info):
            raise RuntimeError('Batch with code [%s] already existed.' % batch_code )

    if (update_sample or update_allele or update_info) and not batch:
        raise RuntimeError('Batch with code [%s] does not exist.' % batch_code)
    elif not batch:
        batch = Batch(  code = batch_code, desc=desc,
                        group_id = group_id, assay_provider_id = assay_provider_id )
        dbsession.add( batch )
        dbsession.flush()

    for k, v in samples.items():

        if 'samples' in v:
            # this is archival format
            sample_set = v['samples']

        else:
            sample_set = { k: v }

        for sample_code, s in sample_set.items():

            print('[INFO] processing sample %s' % sample_code)

            sample = Sample.search( code = sample_code, batch_id = batch.id )

            if (update_allele or update_info) and not sample:
                    raise RuntimeError("sample not found: %s" % sample_code)

            if update_info:
                dict2update_sample( sample, s )
                continue

            if update_sample and sample:
                    raise RuntimeError("sample already existed: %s" % sample_code)

            if not sample:
                 sample = dict2sample( sample_code, s, group_id = group_id, batch = batch,
                            auto = True, sample_class = sample_class,
                            sample_ctxmgr = sample_ctxmgr )

            assays = s['assays']
            for assay_name, a in assays.items():
                print('[INFO] processing assay %s' % assay_name)
                assay = dict2assay( '[%s]' % assay_name, a, auto=True, sample=sample )
                sample.assays.append( assay )
                assay.batch = batch

                dbsession.flush()

                markers = a['markers']
                for marker_name, m in markers.items():

                    marker = Marker.search(marker_name)
                    if not marker:
                        raise RuntimeError("Marker code not found: %s" % marker_name)

                    alleleset = dict2alleleset( m['dye'], assay, marker=marker, auto=True )
                    dbsession.flush()

                    for al in m['alleles']:
                        allele = Allele(
                                    value = al[0],
                                    size = al[1],
                                    height = al[2],
                                    area = al[3],
                                    type_id = EK._id('peak-bin', '@PEAK-TYPE'),
                                    method_id = EK._id('binning-external', '@BINNING-METHOD'),
                                )
                        alleleset.alleles.append( allele )
                        allele.assay = assay
                        allele.sample = sample

                    alleleset.finalized()
                    alleleset.set_latest()
                        
        batch.publish()


