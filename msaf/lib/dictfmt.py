
import csv
import json
import os
from msaf.models import *
from dateutil.parser import parse as parse_date
from datetime import date
from io import StringIO

csv_headers = { 'SAMPLE', 'PANEL', 'ASSAY', 'MARKER', 'DYE', 'NEST', 'STANDARD',
                'COUNTRY', 'ADMINL1', 'ADMINL2', 'ADMINL3', 'ADMINL4', 'COLLECTION_DATE',
                'COMMENTS', 'FSA_COMMENTS' }

csv_alleles = { 'ALLELE', 'HEIGHT', 'AREA', 'SIZE' }

default_date = date(1990,1,1)


def check_csv_headers( fieldnames, csv_headers ):

    # check field names
    for fieldname in fieldnames:
        if fieldname not in csv_headers:
            for csv_allele in csv_alleles:
                if fieldname.startswith( csv_allele ):
                    break
            else:
                raise RuntimeError('CSV headers not recognized: %s' % fieldname)
    return True


def row2sample(r):

    collection_date = parse_date( r.get('COLLECTION_DATE',''), dayfirst=False,
                default=default_date )

    sample = dict(
        
        collection_date = collection_date.strftime('%Y/%m/%d'),
        location = (    r.get('COUNTRY', ''), r.get('ADMINL1',''), r.get('ADMINL2',''),
                        r.get('ADMINL3',''), r.get('ADMINL4','') ),
        comments = r.get('COMMENTS', None),

        assays = {}
    )

    return sample


def reader_from_stream( istream, headers, delimiter ):

    reader = csv.DictReader( istream, delimiter = delimiter )
    check_csv_headers( reader.fieldnames, headers )

    return reader


def csv2dict(istream, with_report=False):

    reader = reader_from_stream( istream, csv_headers )
    log = StringIO() if with_report else None

    return parse_csv( reader, log )


def parse_csv( reader, log, sample_func = None, existing_samples = None ):

    counter = 0

    #prepare allele, height, and area
    allele_field = [ x for x in reader.fieldnames if x.startswith('ALLELE') ]
    height_field = [ x for x in reader.fieldnames if x.startswith('HEIGHT') ]
    area_field = [x for x in reader.fieldnames if x.startswith('AREA') ]
    size_field = [x for x in reader.fieldnames if x.startswith('SIZE') ]

    allele_set = list(zip(allele_field, size_field, height_field, area_field))

    samples = existing_samples or {}

    for row in reader:

        name = row['SAMPLE']

        if name in samples:
            sample = samples[name]
        else:
            # create new sample
            sample = row2sample( row )
            if sample_func:
                sample_func( sample, row )
            samples[name] = sample

        assay_code = row.get('ASSAY', None)
        if assay_code is None:
            continue

        try:
            assay = sample['assays'][assay_code]
        except KeyError:
            assay = dict(
                panel=row['PANEL'],
                nest=row['NEST'],
                size_standard=row['STANDARD'],
                markers = {}
            )
            sample['assays'][assay_code] = assay

        markers = assay['markers']
        marker_name = row['MARKER']
        if marker_name in markers:
            if log:
                print >> log, ( "ERROR: at line %d: duplicate marker name [%s]" %
                        ( counter, marker_name ) )
                return None, log
            else:
                raise RuntimeError('duplicate marker name at line %d!' % counter)

        allele_list = []
        for allele_header, size_header, height_header, area_header in allele_set:
            allele = row[allele_header] or 0
            size = row[size_header] or 0
            height = row[height_header] or 300
            area = row[area_header] or 0
            if int(allele) == 0:
                break
            allele_list.append( (int(allele), float(size), int(height), int(float(area))) )
        markers[marker_name] = dict( dye=row['DYE'], alleles=allele_list )

    return samples, log


def read_dictfile(pathname):
    _, ext = os.path.splitext( pathname )
    if ext == '.json':
        return json.load( open(pathname, 'rt') )
    elif ext == '.yaml':
        return yaml.load( open(pathname, 'rt') )
        

###
### unused below
###

def csv2json(istream, allele_column = 15, with_report=False):

    off = allele_column * 4

    samples = {}

    reader = csv.reader( istream, delimiter=',' )

    header = next(reader)

    if with_report:
        log = StringIO()
    else:
        log = None

    counter = 0
    for row in reader:
        counter += 1
        if len(row) < 82:
            if log:
                print("WARNING: at line %d: appending more fields" % (counter), file=log)
            row += [ None ] * (82 - len(row))
        name = row[1]

        if name in samples:
            sample = samples[name]
        else:
            print( row[14+off] )
            collection_date = parse_date( row[14+off], dayfirst=False )
            age = float(row[12+off])

            sample = dict(
                location=(row[7+off], row[8+off], row[9+off], row[10+off]),
                case_detection = row[11+off],
                yearofbirth = collection_date.year - age,
                age = age,
                gender = row[13+off],
                collection_date = collection_date.strftime('%Y/%m/%d'),
                withdrawal_method = row[15+off],
                blood_storage = row[16+off],
                microscopy_ident = row[17+off],
                pcr_ident = row[18+off],
                pcr_method = row[19+off],
                recurrent = row[20+off],
                comments = row[21+off],
                assays = {}
            )
            samples[name] = sample

        assay_name = row[0]
        try:
            assay = sample['assays'][assay_name]
        except KeyError:
            assay = dict(
                panel=row[2],
                nest=row[5],
                size_standard=row[6],
                markers = {}
            )
            sample['assays'][assay_name] = assay

        markers = assay['markers']
        marker_name = row[3]
        if marker_name in markers:
            if log:
                print >> log, "ERROR: at line %d: duplicate marker name [%s]" % ( counter, marker_name )
                return None, log
            else:
                raise RuntimeError('duplicate marker name at line %d!' % counter)
        allele_list = []
        for allele, size, height, area in zip(
                        row[7:7+allele_column],
                        row[7+allele_column:7+allele_column*2],
                        row[7+allele_column*2:7+allele_column*3],
                        row[7+allele_column*3:7+allele_column*4]):
            if int(allele) == 0:
                break
            allele_list.append( (int(allele), float(size), int(height), int(float(area))) )
        markers[marker_name] = dict( dye=row[4], alleles=allele_list )

    if log:
        return json.dumps( samples ), log
    return json.dumps(samples)


def json2db(jsonfile, update=False, group_id=0):

    samples = json.load(jsonfile)

    if type(samples) == dict:

        for key in samples:
            s = samples[key]

            # get the location first
            location = Location.search( s['location'][0].lower(),
                                        s['location'][1].lower(),
                                        s['location'][2].lower(),
                                        s['location'][3].lower(),
                                        True)

            # for now, subject is similar to sample
            subject = Subject(name = key, gender = s['gender'], yearofbirth = s['yearofbirth'])
            dbsession.add( subject )
            dbsession.flush()

            collection_date = [ int(x) for x in s['collection_date'].split('/') ]

            # TODO:
            # search for sample based on name, gender, collection_date and location_id
            # if not found, create new one
            # if found, then alleles for new markers can be imported (updated)
            # and alleles for existing markers be replaced with new alleles,
            # but will use option in uploading page: upload new markers only, or
            # replace existing markers
            # sample = Sample.search( name, gender, collection_date, location_id )
            # if not sample.id:
            #   sample.age = int(s['age'])
            # ...

            sample = Sample( 
                        name = key,
                        #age = int(s['age']),
                        #gender = s['gender'],
                        collection_date = date(*collection_date),
                        passive_case_detection = s['case_detection'] or None,
                        storage_id = CK._id(s['blood_storage'], '@BLOOD_STORAGE', auto=False),
                        method_id = CK._id(s['withdrawal_method'], '@METHOD', auto=False),
                        location_id = location.id,
                        subject_id = subject.id,
                        group_id = group_id
                    )
            dbsession.add( sample )
            dbsession.flush()

            assays = s['assays']
            for key in assays:
                a = assays[key]
                assay = Assay( sample_id = sample.id,
                                filename = key,
                                nest = (a['nest'] == 'Y'),
                                size_standard_id = CK._id( a['size_standard'] ),
                                panel_id = CK._id( a['panel'] ),
                        )
                dbsession.add( assay )
                dbsession.flush()

                markers = a['markers']
                for marker_name in markers:
                    m = markers[marker_name]
                    markerset = MarkerSet.search( marker_name )

                    marker = Marker( markerset_id = markerset.id, assay_id = assay.id,
                                sample_id = sample.id, dye=m['dye'] )
                    dbsession.add( marker )
                    dbsession.flush()

                    for al in m['alleles']:
                        allele = Allele( markerset_id = markerset.id,
                                        marker_id = marker.id,
                                        assay_id=assay.id,
                                        sample_id = sample.id,
                                        value = al[0],
                                        size = al[1],
                                        height = al[2],
                                        area = al[3]
                                )
                        dbsession.add( allele )
                    dbsession.flush()
 


def db2json( sample ):
    pass


def boolean(text):
    if text is None:
        return None
    if type(text) == str:
        if text[0] == 'Y':
            return True
        else:
            return False

def sample2json( sample ):
    pass

def json2sample( sample_name, data, group_id, auto=True ):
    """ given the data, return the sample """
    
    collection_date = date(*[ int(x) for x in data['collection_date'].split('/') ])
    location = Location.search( *[ x.lower() for x in data['location'] ], auto=auto )

    if not location:
        return None

    sample = Sample.search( name=sample_name,
                            collection_date = collection_date,
                            location_id = location.id,
                            auto = auto )
    if not sample:
        return None

    if not sample.id:
        # new sample submission, import other information
        case_detection = data['case_detection']
        if case_detection:
            case_detection = True if case_detection[0] == 'Y' else False
        else:
            case_detection = None
        sample.passive_case_detection = case_detection
        sample.storage_id = CK._id(data['blood_storage'], '@BLOOD_STORAGE', auto=False)
        sample.method_id = CK._id(data['withdrawal_method'], '@METHOD', auto=False)
        sample.microscopy_ident = data['microscopy_ident'] or None
        sample.pcr_ident = data['pcr_ident'] or None
        sample.pcr_method = data['pcr_method'] or None
        sample.recurrent = boolean(data['recurrent']) or None
        sample.comments = data['comments'] or None
        sample.group_id = group_id
        #raise RuntimeError(sample)
        #dbsession.flush()
        
    return sample


def assay2json( assay ):
    pass

def allele2json( allele ):
    pass

def json2assay( assay_name, data, auto=False ):
    # XXX: need to use search instead of creating new assay
    assay = Assay( filename = assay_name,
                    nest = (data['nest'] == 'Y'),
                    size_standard_id = CK._id( data['size_standard'] ),
                    panel_id = CK._id( data['panel'] ),
        )
    return assay


def json2marker( marker_name, dye, assay, auto=False ):
    # XXX: do we need to search first?
    markerset = MarkerSet.search( marker_name )
    marker = Marker( markerset_id = markerset.id, dye=dye )
    assay.markers.append( marker )
    marker.sample = assay.sample
    return marker


def json2subject(name, sample, auto=False ):

    gender = sample['gender']
    yearofbirth = sample['yearofbirth']
    subject = Subject.search( name = name, gender = gender, yearofbirth = yearofbirth,
                    auto=auto )
    return subject

    

def json2db2( json_stream, batch_code='', desc='', group_id=0, update=False ):

    samples = json.load( json_stream )

    if type(samples) != dict:
        raise RuntimeError('Wrong JSON format. Must be a map/dictionary object')

    batch = Batch( code = batch_code, desc=desc, group_id = group_id )

    for k, v in samples.iteritems():

        subject = json2subject( k, v, auto=True )

        if v.has_key('samples'):
            # this is archival format
            sample_set = v['samples']

        else:
            sample_set = { k: v }

        for sample_name, s in sample_set.iteritems():
            sample = json2sample( sample_name, s, group_id = group_id, auto=True )
            if not sample.subject_id:
                sample.subject = subject
            if not sample.batch_id:
                sample.batch = batch

            assays = s['assays']
            for assay_name, a in assays.iteritems():
                assay = json2assay( assay_name, a, auto=True )
                sample.assays.append( assay )
                assay.batch = batch

                markers = a['markers']
                for marker_name, m in markers.iteritems():
                    marker = json2marker( marker_name, m['dye'], assay, auto=True )

                    for al in m['alleles']:
                        allele = Allele( markerset_id = marker.markerset_id,
                                        value = al[0],
                                        size = al[1],
                                        height = al[2],
                                        area = al[3]
                                )
                        marker.alleles.append( allele )
                        allele.assay = assay
                        allele.sample = sample
                        
        batch.publish()



# TODO
# - update feature (so another json file for other markers can be imported into db,
#   so unique assay/markers depend on sample name, location, and collection_date
# - refactor the library
