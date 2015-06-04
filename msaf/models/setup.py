
from rhombus.models.setup import setup_db as rhombus_setup_db
from rhombus.models import *
from .msdb import *
from msaf.lib.roles import *

def setup_db(*ops):
    """ setup genotypedb database
    """

    rhombus_setup_db(_op_setup, *ops)

    # insert additional CK or other system specific data here

    #get_dbsession().commit()

def bulk_insert(class_, itemlist):
    for item in itemlist:
        class_.from_dict( item )

def _op_setup():
        EK.bulk_insert( msaf_ek )
        Group.bulk_insert( msaf_groups )
        bulk_insert(Panel, panels)
        bulk_insert(Location, locations)


msaf_groups = [
    ( '_DataMgr_', [ DATAADM, DATAVIEW ] ),
    ( '_ProtocolMgr_', [] ),
    ( '_DigitalAssetMgr_', [] ),
    ( '_PanelMgr_', [] ),
]

msaf_ek = [

    ( '@ROLES', None,
        [   (DATAADM, 'data administrative role'),
            (DATAVIEW, 'data viewer role'),
            (BATCH_CREATE, 'create new batch'),
            (BATCH_MODIFY, 'modify batch'),
            (BATCH_VIEW, 'view batch'),
            (BATCH_DELETE, 'delete batch'),
            (MARKER_CREATE, 'create new marker'),
            (MARKER_MODIFY, 'modify marker'),
            (MARKER_VIEW, 'view marker'),
            (MARKER_DELETE, 'delete marker'),
            (LOCATION_CREATE, 'create new location'),
            (LOCATION_MODIFY, 'modify location'),
            (LOCATION_VIEW, 'view location'),
            (LOCATION_DELETE, 'delete location'),
        ]),

    ( '@METADATAKEY', 'metadata key',
        [   ('exclude', 'markers to exclude'),
            ('qcreport', 'quality control report'),
            ('remark', 'additional remark')
        ]),

    ( '@SAMPLE-TYPE', 'sample type',
        [   ('sample-field', 'field sample'),
            ('sample-reference', 'reference sample'),
            ('sample-unsuitable', 'unsuitable sample'),
        ]),

    ( '@LADDER', 'ladder for fragment analysis',
        [   ('ladder-unset', '-'),
            ('LIZ600',  [ 'LIZ 600 ABI standard ladder',
                        '{ "dye": "liz", '
                        '"sizes": [ 20.0, 40.0, 60.0, 80.0, 100.0, 114.0, 120.0, 140.0, 160.0, '
                        '180.0, 200.0, 214.0, 220.0, 240.0, 250.0, 260.0, 280.0, 300.0, '
                        '314.0, 320.0, 340.0, 360.0, 380.0, 400.0, 414.0, 420.0, 440.0, '
                        '460.0, 480.0, 500.0, 514.0, 520.0, 540.0, 560.0, 580.0, 600.0 ] }'] ),
            ( 'LIZ500', [ 'LIZ 500 ABI standard ladder',
                        '{ "dye": "liz", '
                        '"sizes": [ 35, 50, 75, 100, 139, 150, 160, 200, 250, 300, 340, 350, '
                        '400, 450, 490, 500 ] }' ] ),
            ('ROCK500', 'ROCK500 standard ABI ladder')
        ]),

    ( '@ASSAY-STATUS', 'status for each assay',
        [   ('assay-uploaded', 'assay file just uploaded'),
            ('assay-analyzed', 'assay is being analyzed'),
            ('assay-reviewed', 'assay analysis is completed'),
            ('assay-unavailable', 'assay is not available'),
        ]),

    ( '@CHANNEL-STATUS', 'status for each channel',
        [   ('channel-clean', 'clean channel for analysis'),
            ('channel-dirty', 'dirty channel not suitable for analysis'),
            ('channel-ladder', 'channel containing ladder'),
            ('channel-unavailable', 'channel is not available'),
            ('channel-unassigned', 'channel is not assigned')
        ]),

    # for ladder channel:
    # - allele-autoladder
    # when a sample channel is entered, it will be allele-auto or allele-size
    # when a sample channel is adjusted manually, it will be allele-semi
    # when a sample channel is entered via bulk uploading, it will be allele-external

    ( '@ALLELE-METHOD', 'fragment analysis method for each alleleset',
        [   ('allele-autoladder', 'automatic value assignment for ladder'),
            ('allele-semiladder', 'manual adjustment for ladder size determination'),
            ('allele-external', 'external method for manual size determination'),
            ('allele-leastsquare', '3rd order least square fit method'),
            ('allele-localsouthern', 'local southern method'),
            ('allele-cubicspline', 'cubic spline interpolation method'),
            ('allele-unknown', 'unknown method')
        ]),

    ( '@PEAK-TYPE', 'type of each peak/signal',
        [   ('peak-bin', 'binned signal peak'),
            ('peak-called', 'called/sized signal peak'),
            ('peak-scanned', 'scanned signal peak'),
            ('peak-ambiguous', 'peak can be assigned more than one marker'),
            ('peak-stutter', 'stutter peak'),
            ('peak-overlap', 'overlap peak from other dye'),
            ('peak-noise', 'noise peak'),
            ('peak-ladder', 'ladder peak'),
            ('peak-unassigned', 'unassigned peak'),
            ('peak-broad', 'peak is too broad'),
            ('peak-bigdelta', 'delta for peak size and bin is too wide'),
            ('peak-uncalled', 'peak has not been binned/called'),
            ('peak-artifact', 'artifact peak')
        ]),

    ( '@BINNING-METHOD', 'method of peak analysis',
        [   ('binning-auto', 'automatic binning'),
            ('binning-semi', 'adjusted auto binning'),
            ('binning-external', 'using external method for manual binning'),
            ('binning-unavailable', 'binning not performed'),
        ]),

    ( '@DYE', 'name of dye',
        [   ('6-FAM', '-' ),
            ('LIZ', '-' ),
            ('NED', '-' ),
            ('TET', '-' ),
            ('VIC', '-' ),
            ('JOE', '-' ),
            ('PET', '-' ),
        ]),

    ( '@SPECIES', 'species type',
        [   ('X', 'species unspecified'),
        ]),

    ( '@PANEL', 'panel schematic',
        [   ('panel-unset', '-'),
            ('panel-external', 'panel set for external method'),
            ('panel-test', [ 'panel for software testing',
                "{ 'codes': {'6-FAM':'B','LIZ':'O','NED':'Y','VIC':'G','PET':'R'},"
                " 'ladder': 'liz600',"
                " 'markers': {'6-FAM': 'pv3.27' } }"
                ]),
        ]),

    ( '@REGION', 'region',
        [ ( '-', 'Region not available'),
        ]),

]


locations = [   dict( country='-', adminl1='-', adminl2='-', adminl3='-', adminl4='-' ),
            ]

markers = [ ('undefined', '-', '-', '-', False, None, None, 0, 0, 0, 'X'),
            ]

panels = [  dict( code='unset', desc='No panel set', data=None,
                    group = '_PanelMgr_', assay_provider = '_PanelMgr_'),
            dict( code='external', desc='panel set for external method', data=None,
                    group = '_PanelMgr_', assay_provider = '_PanelMgr_' ),
            ]

##
## 6-FAM - B
## LIZ - O
## NED - Y
## VIC - G
## PET - R
## TET - ?
## JOE - ?

