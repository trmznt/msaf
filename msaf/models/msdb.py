__copyright__ = '''
msaf/models/msdb.py - part of MsAF

(c) 2012 - 2014 Hidayat Trimarsanto <anto@eijkman.go.id> / <trimarsanto@gmail.com>

All right reserved.
This software is licensed under GPL v3 or later version.
Please read the README.txt of this software.
'''

__version__ = '2014060601'

# TODO:
# next iteration of schema:
#       - add tsize (transformed size),
#         and think about using cubic spline to transform real size to tsize


from rhombus.models.core import *
from rhombus.models.ek import EK
from rhombus.models.user import User, Group
from rhombus.models.mixin import *

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import func

import io, yaml

from msaf.lib.fatools import fautils

# numpy-based array column

import numpy, copy

class NPArray(types.TypeDecorator):
    impl = types.LargeBinary

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        #buf = value.tostring()
        buf = io.BytesIO()
        numpy.save(buf, value)
        return buf.getvalue()

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        buf = io.BytesIO(value)
        return numpy.load(buf)
        #return numpy.fromstring(value)

    def copy_value(self, value):
        return copy.deepcopy( value )


@registered
class Batch(BaseMixIn, Base):
    """ Batch
        
        This class is a container for samples with similar setting, such as samples
        within a site study, or same machines, etc. This class can be extended to
        contain other information, such as site study information or other technical
        data such as capillary machine information.
    """

    __tablename__ = 'batches'

    code = Column(types.String(32), unique=True, nullable=False)
    """ unique batch code """

    published = Column(types.Boolean, nullable=False, default=False)
    """ whether this batch of samples has been published """

    shared = Column(types.Boolean, nullable=False, default=False)
    """ whether this batch of samples has been shared (viewable/searchable by other
        users
    """

    group_id = Column(types.Integer, ForeignKey('groups.id'), nullable=False)
    group = relationship(Group, uselist=False, foreign_keys=group_id)

    assay_provider_id = Column(types.Integer, ForeignKey('groups.id'), nullable=False)
    assay_provider = relationship(Group, uselist=False, foreign_keys=assay_provider_id)

    desc = deferred(Column(types.Text(), nullable=False, default=''))
    """ description of this batch """

    yaml = deferred(Column(YAMLCol(1024), nullable=False, default=''))
    """ yaml data """


    def __repr__(self):
        return "<BATCH [%s]>" % self.code

    def update(self, obj):
        """ update current object with values from obj """
        self.code = obj.code
        self.desc = obj.desc
        self.group_id = obj.group_id
        self.assay_provider_id = obj.assay_provider_id

    def publish(self):
        self.published = True

    def is_authorized(self, group_ids):
        return self.group_id in group_ids

    def reset_samples(self):
        """ reset / remove all samples registered for this batch
        """
        for sample in self.samples:
            sample.reset_assays()
        

    @staticmethod
    def search( code = None):
        q = Batch.query()
        if code:
            q = q.filter( Batch.code == code )
        r = q.all()
        if len(r) == 0:
            return None
        if len(r) == 1:
            return r[0]
        return r


@registered
class BatchEnumData(EnumDataMixIn, Base):
    """ SampleEnumData

        This class holds enumerated data from corresponding batch.
    """
    __tablename__ = 'batchenums'
    
    batch_id = Column(types.Integer, ForeignKey('batches.id', ondelete='CASCADE'),
                        nullable=False )
    batch = relationship(Batch, uselist=False, backref=backref('enums', lazy='dynamic'))

    __table_args__ = ( UniqueConstraint('cat_id', 'batch_id'), {} )


@registered
class BatchStringData(StringDataMixIn, Base):
    """ BatchStringData

        This class holds categorical string data from corresponding batch.
    """
    __tablename__ = 'batchstrings'

    batch_id = Column(types.Integer, ForeignKey('batches.id', ondelete='CASCADE'),
                        nullable=False )
    batch = relationship(Batch, uselist=False,
                backref=backref('strings', lazy='dynamic', passive_deletes=True))

    __table_args__ = ( UniqueConstraint('cat_id', 'batch_id'), {} )


@registered
class Location(BaseMixIn, Base):
    """ regions """

    __tablename__ = 'locations'

    country_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    level1_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    level2_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    level3_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    level4_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    """ location information """

    country = EK.proxy('country_id', '@REGION')
    level1 = EK.proxy('level1_id', '@REGION')
    level2 = EK.proxy('level2_id', '@REGION')
    level3 = EK.proxy('level3_id', '@REGION')
    level4 = EK.proxy('level4_id', '@REGION')

    latitude = Column(types.Float, nullable=False, default=0)
    """ latitude of location/site """

    longitude = Column(types.Float, nullable=False, default=0)
    """ longitude of location/site """

    altitude = Column(types.Float, nullable=False, default=0)
    """ altitute of location/site """

    notes =  Column(types.String(128), nullable=False, default='')
    """ some notes about the location """

    __table_args__ = ( 
        UniqueConstraint('country_id', 'level1_id', 'level2_id', 'level3_id', 'level4_id'),
        {} )

    @staticmethod
    def search(country, level1='', level2='', level3='', level4='', auto=False):
        country_id = EK._id(country, '@REGION', auto)
        level1_id = EK._id(level1, '@REGION', auto)
        level2_id = EK._id(level2, '@REGION', auto)
        level3_id = EK._id(level3, '@REGION', auto)
        level4_id = EK._id(level4, '@REGION', auto)

        q = Location.query().filter(
                and_(Location.country_id == country_id,
                        Location.level1_id == level1_id,
                        Location.level2_id == level2_id,
                        Location.level3_id == level3_id,
                        Location.level4_id == level4_id) )
        r = q.all()
        if len(r) == 0 and auto:
            location = Location( country_id = country_id,
                                level1_id = level1_id,
                                level2_id = level2_id,
                                level3_id = level3_id,
                                level4_id = level4_id )
            dbsession.add( location )
            dbsession.flush()

            return location

        return r[0]


    @staticmethod
    def grep(term):
        regions = EK.get_members('@REGION').filter( EK.key.contains( term.lower() ) )
        ids = [ r.id for r in regions ]
        return Location.query().filter(
            or_( Location.country_id.in_( ids ), Location.level1_id.in_( ids ),
                Location.level2_id.in_( ids ), Location.level3_id.in_( ids ),
                Location.level4_id.in_( ids ) ) )


    def render(self, level=4):
        level = int(level)
        if level < 0:
            return ''
        names = [ self.country ]
        if level >= 1 and self.level1:
            names.append( self.level1 )
        if level >= 2 and self.level2:
            names.append( self.level2 )
        if level >= 3 and self.level3:
            names.append( self.level3 )
        if level >= 4 and self.level4:
            names.append( self.level4 )
        return ' / '.join( names )


    def __repr__(self):
        return '<Location: %s>' % self.render()


    def sample_count(self):
        return self.samples.count()


    @staticmethod
    def from_dict(d, update=False):
        return Location.search( d['country'], d['adminl1'], d['adminl2'],
                                d['adminl3'], d['adminl4'], auto=True )

@registered
class Sample(BaseMixIn, Base):
    """ Sample

        This class contains basic information regarding the relationship of each sample
        with the rest of the class/object in the database. Any other information about
        the sample should be provided in the extended column data or in the inherited class.
    """

    __tablename__ = 'samples'

    code = Column(types.String(32), nullable=False)
    """ sample code, unique for each batch """

    instcode = deferred( Column(types.String(32), nullable=True) )
    """ original institutional code """

    label = deferred( Column(types.String(16), nullable=False, default='') )
    altlabel = deferred( Column(types.String(16), nullable=False, default='') )
    """ labeling and alternate labeling """

    batch_id = Column(types.Integer, ForeignKey('batches.id', ondelete='CASCADE'),
            nullable=False)
    batch = relationship(Batch, uselist=False,
            backref=backref("samples", lazy='dynamic', passive_deletes=True))
    """ relation to batch, with cascading delete i.e. this sample will be deleted if the
        corresponding batch is deleted
    """

    type_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    type = EK.proxy('type_id')

    shared = Column(types.Boolean, nullable=False, default=False)
    """ whether this particular sample has been shared (viewable/searchable by other
        users), necessary so that individual sample can be shared without all samples
        within a group being shared)
    """

    collection_date = Column(types.Date, nullable=False)
    """ the date of the sample collection """

    location_id = Column(types.Integer, ForeignKey('locations.id'), nullable=False)
    location = relationship(Location, uselist=False,
            backref=backref("samples", lazy='dynamic', passive_deletes=True))
    """ relation to location, with cascading delete """

    latitude = Column(types.Float, nullable=False, default=0)
    """ exact latitude of the sample """

    longitude = Column(types.Float, nullable=False, default=0)
    """ exact longitude of the sample """

    altitude = Column(types.Float, nullable=False, default=0)
    """ exact altitute of the sample """

    comments = deferred( Column(types.Text(), nullable=False, default='') )

    trashed = Column(types.Boolean, nullable=False, default=False)
    """ whether this sample has been marked as deleted """

    polymorphic_type = Column(types.Integer, nullable=False, default=0)

    __mapper_args__ = { 'polymorphic_on': polymorphic_type }

    __table_args__ = (  UniqueConstraint( 'code', 'batch_id' ), {} )

    def __repr__(self):
        return "<Sample [%s] from batch [%s]>" % (self.code, self.batch.code)

    def _get_markers(self):
        """ return AlleleSet query for this sample """
        return AlleleSet.query().join(Channel).join(Assay).join(Sample).filter( Sample.id == self.id )
    markers = property(_get_markers)

    def update(self, obj):
        if obj.batch_id is not None:
            self.batch_id = obj.batch_id
        if obj.code:
            self.code = obj.code
        if obj.type_id is not None:
            self.type_id = obj.type_id
        if obj.shared is not None:
            self.shared = obj.shared
        if obj.collection_date:
            self.collection_date = obj.collection_date
        if obj.location_id is not None:
            self.location_id = obj.location_id
        if obj.comments:
            self.comments = obj.comments


    def is_authorized(self, group_ids):
        return self.batch.is_authorized( group_ids )


    def get_alleles(self, marker_ids = None):

        q = dbsession.query( Allele.value, Allele.height, AlleleSet.marker_id )
        q = q.join( AlleleSet ).filter( AlleleSet.sample_id == self.id )
        q = q.order_by( AlleleSet.marker_id, Allele.height.desc() )
        #q = q.filter( AlleleSet.latest == True )
        q = q.filter( Allele.type_id.in_( [ EK._id('peak-bin'), EK._id('peak-called')] ))
        if marker_ids:
            q = q.filter( AlleleSet.marker_id.in_( marker_ids ) )

        alleles = []
        current_alleles = None
        current_marker = 0
        for (value, height, marker_id) in q:
            if marker_id == 0:
                continue
            if marker_id != current_marker:
                if current_marker != 0: 
                    alleles.append( (current_marker, current_alleles) )
                current_marker = marker_id
                current_alleles = [ (value, height) ]
            else:
                current_alleles.append( (value, height) )

        if current_marker != 0:
            alleles.append( (current_marker, current_alleles) )

        return alleles


    def reset_assays(self):
        """ remove all assays registered for this sample
        """
        for assay in self.assays:
            dbsession.delete( assay )
        dbsession.flush()

    @staticmethod
    def search( code, batch_id ):
        if batch_id is None:
            raise RuntimeError( "Sample.search() needs a supplied batch_id" )

        q = Sample.query().filter( Sample.code == code, Sample.batch_id == batch_id )
        r = q.all()
        if len(r) == 0:
            return None
            raise RuntimeError('Sample not found')
        if len(r) > 1:
            raise RuntimeError('Found multiple sample')
        return r[0]



@registered
class SampleEnumData(EnumDataMixIn, Base):
    """ SampleEnumData

        This class holds enumerated data from corresponding sample.
    """
    __tablename__ = 'sampleenums'

    sample_id = Column(types.Integer, ForeignKey('samples.id', ondelete='CASCADE'),
                        nullable=False)
    sample = relationship(Sample, uselist=False,
            backref=backref('enums', lazy='dynamic', passive_deletes=True))


@registered
class SampleStringData(StringDataMixIn, Base):
    """ SampleStringData

        This class holds categorical string data from corresponding sample.
    """
    __tablename__ = 'samplestrings'

    sample_id = Column(types.Integer, ForeignKey('samples.id', ondelete='CASCADE'),
                        nullable=False)
    sample = relationship(Sample, uselist=False,
            backref=backref('strings', lazy='dynamic', passive_deletes=True))

    __table_args__ = ( UniqueConstraint('cat_id', 'sample_id'), {} )


@registered
class AssayStringData(StringDataMixIn, Base):
    """ SampleStringData

        This class holds categorical string data from corresponding assay.
    """
    __tablename__ = 'assaystrings'

    assay_id = Column(types.Integer, ForeignKey('assays.id', ondelete='CASCADE'),
                        nullable=False)

    __table_args__ = ( UniqueConstraint('cat_id', 'assay_id'), {} )


@registered
class Assay(BaseMixIn, Base):
    """ Assay

        This class holds raw assay data.
    """

    __tablename__ = 'assays'
    """ mapper tablename """

    sample_id = Column(types.Integer, ForeignKey('samples.id', ondelete='CASCADE'),
                nullable=False)
    sample = relationship(Sample, uselist=False,
            backref=backref('assays', lazy='dynamic', cascade='all, delete-orphan',
                        passive_deletes=True))
    """ sample id """

    filename = Column(types.String(128), nullable=False)
    """ original FSA filename of the assay """

    size_standard_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    size_standard = EK.proxy('size_standard_id')
    """ EK of size standard, under @LADDER """

    panel_id = Column(types.Integer, ForeignKey('panels.id'), nullable=False)
    #panel = EK.proxy('panel_id')
    panel = relationship('Panel', uselist=False)
    """ EK of panel, under @PANEL """

    status_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    status = EK.proxy('status_id')
    """ EK of assay status, under @ASSAY-STATUS """

    assay_provider_id = Column(types.Integer, ForeignKey('groups.id'), nullable=False)
    assay_provider = relationship(Group, uselist=False)
    """ group/centre/institute that provides the genotyping / assay """

    notes = deferred(Column(types.Text(), nullable=False, default=''))


    rawdata = deferred(Column(types.Binary(), nullable=False))
    """ raw data for this assay (FSA file content) """

    score = Column(types.Float, nullable=False, default=-1)
    """ ladder QC score for this assay """

    dpscore = Column(types.Float, nullable=False, default=-1)
    """ DP score for ladder alignment """

    z = deferred(Column(NPArray))
    """ curve polynomial estimation """

    rss = Column(types.Float, default = -1)
    """  residual sum of squar, rss = SUM[ abs(z(x) - y)**2 ] """

    avg_ladder_peaks = Column(types.Float, nullable=False, default = 0)
    """ average strength of ladder peaks """

    dilution = Column(types.Integer, nullable=False, default=1)
    """ sample dilution """

    sanity_checked = Column(types.Boolean, nullable=False, default=False)
    """ whether this assay has passed all sanity checks """

    trashed = Column(types.Boolean, nullable=False, default=False)
    """ whether this assay has been marked as deleted """


    strings = AssayStringData.interface('assay_id')

    def _get_markers(self):
        return AlleleSet.query().join(Channel).join(Assay).filter( Assay.id == self.id )
    markers = property(_get_markers)


    def is_authorized(self, group_ids):
        return self.sample.is_authorized( group_ids )


    def update(self, obj):
        if obj.panel_id:
            self.panel_id = obj.panel_id
        if obj.size_standard_id:
            self.size_standard_id = obj.size_standard_id


    def create_channels(self, panel_data=None, excluded_markers=None):
        """ separate channels, and assign ladder channel & markers
        """
        from msaf.lib.fatools import traceio, traceutils
        t = traceio.read_abif_stream( io.BytesIO( self.rawdata ) )
        #raise RuntimeError(t)
        channels = traceutils.separate_channels( t )
        for (n, wl, raw, sg) in channels:
            # TODO: should check n (dye name) first in CKs
            c = Channel( raw_data = raw, data = sg, dye = n, wavelen = wl,
                status = 'channel-unassigned', marker = Marker.search('undefined'),
                median=int(numpy.median(raw)), mean=float(raw.mean()),
                max_height=int(raw.max()), std_dev = float(raw.std()) )
            self.channels.append( c )

        self.assign_channels(panel_data, excluded_markers)


    def assign_channels(self, panel = None, excluded_markers=None):
        """ assign ladder channel & marker channels
        """

        if panel is not None:
            # sanity check
            if panel != self.panel:
                raise RuntimeError(
                    'ERR: inconsistence panel definition during channel assignment of assay %s'
                    % self.filename
                )
        else:
            # get panel_data from current panel
            panel = self.panel

        if panel.data is None:
            return

        panel_data = panel.data

        ladder = EK.get(EK.getid( panel_data['ladder'] ))
        ladder_data = json.loads( ladder.data.decode('UTF-8') )
        ladder_dye = ladder_data['dye']

        print('excluded markers:', excluded_markers)

        for channel in self.channels:
            if channel.dye.upper() == ladder_dye.upper():
                channel.status = 'channel-ladder'
                self.size_standard_id = ladder.id
            else:
                status = 'channel-clean'
                try:
                    marker_code = panel.get_marker(channel.dye.upper())
                except KeyError:
                    marker_code = 'undefined'
                    status = 'channel-unassigned'
                if excluded_markers and marker_code.lower() in excluded_markers:
                    marker_code = 'undefined'
                    status = 'channel-unassigned'
                marker = Marker.search(marker_code)
                #channel.marker = marker
                channel.set_marker( marker )
                channel.status = status
                print('assigning dye %s -> %s' % (channel.dye, marker_code))


    def estimate_z(self):
        """ estimate z, rss & score based on peak-ladder only
        """

        # find the ladder
        ladder = self.get_ladder()
        if not ladder:
            raise RuntimeError( 'ladder channel for this assay is not found' )

        peak_pairs = [ (a.size, a) for a in ladder.get_latest_alleleset().alleles
                        if a.type == 'peak-ladder' ]

        self.z, self.rss = fautils.estimate_z( peak_pairs )
        ladder_spec = EK.get( self.size_standard_id )
        ladder_data = ladder_spec.data_from_json()
        ladder_sizes = ladder_data['sizes']
        self.score, reports = fautils.score_ladder(self.rss, len(peak_pairs), len(ladder_sizes))

        self.strings['qcreport'] = '|'.join(reports)


    def set_ladder_xxx(self, ladder_id):
        """ set the ladder and calculate Z and RSS
            return quality status
            
        """
    
        # clear channel
        for channel in self.channels.filter( Channel.status_id == EK._id('channel-ladder') ):
            channel.status = 'channel-clean'

        ladder_spec = EK.get(ladder_id)
        self.size_standard_id = ladder_id
        if ladder_spec.key == 'ladder-unset':
            return

        ladder_data = json.loads( ladder_spec.data.decode('UTF-8') )
        dye = ladder_data['dye']
        ladder = self.channels.filter( Channel.dye_id == EK._id( dye ) ).one()
        ladder.status = 'channel-ladder'

        # get the smallest rss, which is the first result of fin_ladder_peaks
        ladder_peaks, z, rss = ladder.find_ladder_peaks( ladder_data['sizes'] )[0]
        ladder.assign_ladder_peaks( ladder_peaks )

        self.z = z
        self.rss = rss

        quality_score = 1.0
        if rss <= 0 or rss > 225:
            quality_score -= 0.25
        if len(ladder_peaks)/len(ladder_data['sizes']) < 0.75:
            quality_score -= 0.25
        return quality_score


    def set_ladder(self, ladder_ek_id):
        """ assign ladder channel
        """

        # clear channel
        for channel in self.channels.filter( Channel.status_id == EK.getid('channel-ladder') ):
            channel.status = 'channel-clean'

        ladder_spec = EK.get(ladder_ek_id)
        self.size_standard_id = ladder_ek_id
        if ladder_spec.key == 'ladder-unset':
            return

        ladder_data = json.loads( ladder_spec.data.decode('UTF-8') )
        dye = ladder_data['dye']
        ladder = self.channels.filter( Channel.dye_id == EK.getid( dye ) ).one()
        ladder.status = 'channel-ladder'


    def get_ladder(self):
        """ get ladder channel
        """
        return self.channels.filter( Channel.status_id == EK._id( 'channel-ladder' ) ).one()


    def scan_ladder_peaks(self, parameter=None, reset=False):
        """ scan ladder peaks with supplied parameter, or use default
            calculate z, rss & score
        """
        ladder_channel = self.get_ladder()
        ladder = EK.get(self.size_standard_id)
        ladder_data = ladder.data_from_json()

        if reset:
            ladder_channel.reset()
        (z, rss, score, dpscore, reports, ladder_alleles) = ladder_channel.scan_ladder_peaks(
                ladder_data['sizes'], parameter )
        self.z = z
        self.rss = rss
        self.score = score
        self.dpscore = dpscore
        self.strings['qcreport'] = '|'.join( reports )

        return (score, ladder_alleles)


    def scan_peaks_xxx(self, parameter=None, ladder_alleles=None, method='cubicspline'):
        """ scan and call peaks
        """

        from msaf.lib.fatools import fautils

        if parameter is None:
            parameter = fautils.ScanningParameter()

        if ladder_alleles is None:
            ladder_alleles = [ a for a in self.get_ladder().get_latest_alleleset().alleles
                                if a.type == 'peak-ladder' or a.value > 0 ]
            ladder_alleles.sort( key = lambda x: x.size )

        channels = [ c for c in self.channels if c.status != 'channel-ladder' ]

        if method == 'cubicspline':
            func = fautils.cubic_spline( ladder_alleles )
            method_type = 'allele-cubicspline'
        elif method == 'leastsquare':
            func = fautils.least_square( self.z )
            method_type = 'allele-leastsquare'
        else:
            raise RuntimeError('ERR - calling method not known: %s' % method)

        allelesets = []
        for c in channels:
            c.reset()
            alleleset = c.scan_peaks(func, parameter)
            alleleset.method = method_type
            alleleset.marker_id = c.marker_id
            allelesets.append( alleleset )

        fautils.check_overlap_peaks( allelesets, threshold = parameter.overlap_threshold )


    def scan_peaks(self, parameter=None):
        """ scan all peaks in all channels except channel ladder
            sizing and checking for overlaps/stutter are performed by call_peaks()
            return a list of 
        """

        from msaf.lib.fatools import fautils

        if parameter is None:
            parameter = fautils.ScanningParameter()

        channels = [ c for c in self.channels if c.status != 'channel-ladder' ]

        allelesets = []
        for c in channels:
            c.reset()
            alleleset = c.scan_peaks(parameter)
            allelesets.append( alleleset )

        return allelesets


    def call_peaks(self, method='cubicspline', parameter=None):

        from msaf.lib.fatools import fautils

        if parameter is None:
            parameter = fautils.ScanningParameter()

        ladder_channel = None
        channels = []
        for c in self.channels:
            if c.status == 'channel-ladder':
                ladder_channel = c
            else:
                channels.append( c )

        if ladder_channel is None:
            raise RuntimeError('INCONSISTENCY ERR: no ladder found')

        if method == 'cubicspline':
            ladder_alleles = [ p for p in ladder_channel.alleles if p.type == 'peak-ladder' ]
            ladder_alleles.sort( key = lambda p: p.size )
            func = fautils.cubic_spline( ladder_alleles )
        else:
            raise RuntimeError('METHOD UNKNOWN')

        allelesets = []
        for c in channels:
            alleles = c.call_peaks( func, ladder_alleles, parameter )
            allelesets.append( alleles )

        #fautils.check_overlap_peaks( channels, parameter.overlap_threshold )

        return allelesets


    def bin_peaks(self, markers=None):
        
        if markers:
            marker_ids = list( m.id for m in markers )
        else:
            marker_ids = None

        for c in self.channels:
            if c.status == 'channel-ladder':
                continue
            if marker_ids and c.marker_id not in marker_ids:
                continue

            c.bin_peaks()


    def reset(self):
        self.score = 0
        self.z = None
        self.rss = -1
        for channel in self.channels:
            channel.reset()



@registered
class Marker(BaseMixIn, Base):
    """ Marker

        This hold marker (or probe) information.
    """
    __tablename__ = 'markers'

    code = Column(types.String(32), nullable=False, unique=True)
    """ marker name/code """
    
    locus = Column(types.String(32), nullable=False, default='')
    """ locus/gene/region name """
    
    primer_1 = Column(types.String(48), nullable=False, default='')
    """ 1st primer, use | to separate forward/reverse primers """
    
    primer_2 = Column(types.String(48), nullable=False, default='')
    """ 2nd/nested primer, if available """
    
    repeats = Column(types.Integer, nullable=False, default=2)
    """ repeats of the marker """
    
    nested = Column(types.Boolean, nullable=False, default=False)
    """ true if nested primers """

    species_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    species = EK.proxy('species_id')
    """ species of this marker """
    
    desc = deferred(Column(types.Text(), nullable=False, default=''))
    """ description """

    min_size = Column(types.Integer, nullable=False, default=0)
    max_size = Column(types.Integer, nullable=False, default=0)
    """ range of allele size for this marker """

    bins = deferred(Column(YAMLCol(2048), nullable=False, default=''))
    """ sorted known bins for this markers """
    
    related_to_id = Column(types.Integer, ForeignKey('markers.id'),
                          nullable=True)
    related_to = relationship("Marker", uselist=False)
    """ points to related marker """
    
    z_params = Column(types.String(32), nullable=True)
    """ mathematical expression correlating with the related_to marker """


    def update(self, obj):
        if obj.min_size is not None:
            self.min_size = obj.min_size
        if obj.max_size is not None:
            self.max_size = obj.max_size
        if obj.repeats is not None:
            self.repeats = obj.repeats
        if obj.bins is not None:
            self.bins = obj.bins


    @staticmethod
    def search(code):
        """ provide case-insensitive search for marker code """
        q = Marker.query().filter( func.lower(Marker.code) == func.lower(code) )
        return q.one()


    @staticmethod
    def bulk_insert(markers):
        """ [ (code, gene, primer_1, primer_2, nested, related_to, desc,
            repeats, min, max, species ] """
        for m in markers:
            marker = Marker(    code=m[0], locus=m[1],
                                primer_1=m[2], primer_2=m[3], nested=m[4],
                                desc=m[6],
                                repeats=m[7], min_size=m[8], max_size=m[9],
                                species_id = EK._id(m[10], '@SPECIES') )
            if m[5]:
                # perform lookup and get id
                pass
            dbsession.add( marker )


    @staticmethod
    def dump(_out, query=None):
        """ dump data as YAML """
        if not query:
            query = Marker.query()
        yaml.safe_dump_all( (m.as_dict() for m in query), _out,
            default_flow_style=False )


    @staticmethod
    def load_all(yamldata):
        l = yaml.safe_load_all(yamldata)
        for m in l:
            Marker.from_dict(m)
            dbsession.flush()


    def as_dict(self):
        d = dict( code = self.code, locus = self.locus,
                primer_1 = self.primer_1, primer_2 = self.primer_2,
                repeats = self.repeats, nested = self.nested,
                desc = self.desc, species = self.species,
                min_size = self.min_size, max_size = self.max_size,
                bins = self.bins)
        if self.related_to:
            d['related_to'] = self.relate_to.code
            d['z_params'] = self.z_params
        return d


    @staticmethod
    def from_dict(marker, update = False):
        m = Marker( code = marker['code'], locus = marker['locus'],
                primer_1 = marker['primer_1'], primer_2 = marker['primer_2'],
                repeats = marker['repeats'],
                nested = marker['nested'],
                desc = marker['desc'], species_id = EK._id( marker['species'], '@SPECIES' ),
                min_size = int(marker['min_size']), max_size = int(marker['max_size']),
                bins = marker['bins'])
        related_to = marker.get('related_to', None)
        if related_to:
            m.related_to_id = Marker.search(related_to)
            m.z_params = marker['z_params']

        if update:
            db_marker = Marker.search(m.code)
            db_marker.update( m )
        else:
            dbsession.add( m )
            dbsession.flush()
            db_marker = m

        return db_marker

        dbsession.add( m )
        return m


    def sample_count(self):
        return self.alleleset.count()


    def sample_with_allele_count(self):
        c = 0
        for m in self.markers:
            if len(m.alleles) > 0:
                c += 1
        return c


@registered
class MarkerStringData(StringDataMixIn, Base):
    """ SampleStringData

        This class holds categorical string data from corresponding marker.
    """
    __tablename__ = 'markerstrings'

    marker_id = Column(types.Integer, ForeignKey('markers.id', ondelete='CASCADE'),
                        nullable=False)
    marker = relationship(Marker, uselist=False,
            backref=backref('strings', lazy='dynamic', passive_deletes=True))


@registered
class Panel(BaseMixIn, Base):
    """ Panel

        This class holds panel information
    """
    __tablename__ = 'panels'

    code = Column(types.String(8), nullable=False, unique=True)

    group_id = Column(types.Integer, ForeignKey('groups.id'), nullable=False)
    group = relationship(Group, uselist=False, foreign_keys = group_id)

    assay_provider_id = Column(types.Integer, ForeignKey('groups.id'), nullable=False)
    assay_provider = relationship(Group, uselist=False, foreign_keys = assay_provider_id)

    desc = Column(types.Text(), nullable=False, default='')

    data = Column(YAMLCol(1024), nullable=False)

    # data:
    #  - marker_code
    #    - dye: 6-FAM
    #    - primers: atctgctg / cgatcgtcgct


    def __repr__(self):
        return '<Panel: %s>' % self.code

    @staticmethod
    def search(code):
        """ provide case-insensitive search for marker code """
        q = Panel.query().filter( func.lower(Panel.code) == func.lower(code) )
        return q.one()


    def update(self, ob):
        if self.code != ob.code:
            raise RuntimeError('ERR: attempting to update Panel with different code')
        if ob.desc is not None:
            self.desc = ob.desc
        if ob.group_id is not None:
            self.group_id = ob.group_id
        if ob.assay_provider_id is not None:
            self.assay_provider_id = ob.assay_provider_id
        if ob.data is not None:
            self.data = ob.data


    def as_dict(self):
        return dict(  id = self.id, code = self.code,
                    group = self.group.name if self.group else None,
                    assay_provider = self.assay_provider.name if self.assay_provider else None,
                    desc = self.desc, data = self.data )

    @staticmethod
    def from_dict(d, update=False):
        panel = Panel()
        panel.code = d['code']
        panel.desc = d.get('desc', None)
        panel.data = d.get('data', None)
        panel.group_id = Group.search( d['group'] ).id
        panel.assay_provider_id = Group.search( d['assay_provider'] ).id

        if update:
            db_panel = Panel.search(panel.code)
            db_panel.update( panel )
        else:
            dbsession.add( panel )
            dbsession.flush()
            db_panel = panel

        return db_panel


    def get_marker(self, dye_name):
        markers = self.data['markers']
        for m in markers:
            if markers[m]['dye'] == dye_name:
                return m
        raise KeyError


@registered
class GelImage(BaseMixIn, Base):

    __tablename__ = 'gelimages'

    batch_id = Column(types.Integer, ForeignKey('batches.id', ondelete='CASCADE'),
                    nullable=False)

    filename = Column(types.String(128), nullable=False, default='')

    bindata = Column(types.Binary, nullable=False, default=b'')

    type_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    type = EK.proxy('type_id', '@FILETYPE')
    """ type of the file """


    __table_args__ = ( UniqueConstraint('batch_id', 'filename'), {} )

    

@registered
class GelIMageInfo(BaseMixIn, Base):
    
    __tablename__ = 'gelimageinfos'

    gelimage_id = Column(types.Integer, ForeignKey('gelimages.id', ondelete='CASCADE'),
                    nullable=False)

    sample_id = Column(types.Integer, ForeignKey('samples.id', ondelete='CASCADE'),
                    nullable=False)

    marker_id = Column(types.Integer, ForeignKey('markers.id', ondelete='CASCADE'),
                    nullable=False)

    lane = Column(types.Integer, nullable=False, default=-1)

    notes = Column(types.String(256), nullable=False, default='')

    __table_args__ = ( UniqueConstraint('gelimage_id', 'sample_id', 'marker_id', 'lane'), {} )


@registered
class Channel(BaseMixIn, Base):
    """ Channel
    
        This class holds the channel information of each assay.
    """
    __tablename__ = 'channels'

    assay_id = Column(types.Integer, ForeignKey('assays.id', ondelete='CASCADE'),
                        nullable=False)
    assay = relationship(Assay, uselist=False,
                backref=backref('channels', lazy='dynamic', passive_deletes=True))

    wavelen = Column(types.Integer, nullable=False)
    """ length of wavelen of this channel """

    dye_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    dye = EK.proxy('dye_id')
    """ name of dye for this channel, under @DYE """

    marker_id = Column(types.Integer, ForeignKey('markers.id'), nullable=False)
    marker = relationship(Marker, uselist=False,
                    backref=backref('channels', lazy='dynamic'))
    """ link to marker """

    status_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    status = EK.proxy('status_id')
    """ channel's state under @CHANNEL-STATUS, good-channel, bad-channel, upload-channel """

    raw_data = deferred(Column(NPArray, nullable=False))
    """ raw data from channel as numpy array, can have empty array to accomodate
        allele data from CSV uploading """


    median = Column(types.Integer, nullable=False, default=0)
    mean = Column(types.Float, nullable=False, default=0.0)
    std_dev = Column(types.Float, nullable=False, default=0.0)
    max_height = Column(types.Integer, nullable=False, default=-1)
    min_height = Column(types.Integer, nullable=False, default=-1)
    """ basic descriptive statistics for data"""
        
    data = deferred(Column(NPArray, nullable=False))
    """ data after smoothed using savitzky-golay algorithm and baseline correction
        using top hat morphologic transform
    """


    def find_peaks( self, min_height=50 ):
        """ return a list of [ (size, height, area), ... ] """

        from msaf.lib.microsatellite import peakutils3 as peakutils

        return peakutils.find_peaks( self.data, min_height )


    def find_ladder_peaks( self, ladder = None, min_height = 30, relative_min = 0.50,
                relative_max = 4):
        """ return ( [ (value, size, peak, height, area), ... ], Z, rss )
            with value == size
        """

        from msaf.lib.microsatellite import peakutils3 as peakutils

        if ladder is None:
            ladder_id = self.assay.size_standard_id
            ladder_spec = EK.get(ladder_id)
            if ladder_spec.key == 'ladder-unset':
                raise RuntimeError("ladder hasn't been set for assay %s" % self.assay.filename)
            ladder_data = json.loads( ladder_spec.data.decode('UTF-8') )
            ladder = ladder_data['sizes']

        return peakutils.find_ladder_peaks( self.data, ladder, min_height = min_height,
                relative_min = relative_min, relative_max = relative_max )


    def assign_ladder_peaks( self, peaks, method='allele-autoladder' ):
        """ reset the peaks for this channel, create a new alleleset and
            populate with the peaks
        """

        self.reset_peaks()
        method_id = EK._id(method)
        
        ladder_peaks = [ (v, s, p, h, a, 'peak-ladder', 'undefined', method) for 
                v, s, p, h, a in peaks ]

        self.assign_complete_peaks( ladder_peaks, method )


    def assign_peaks(self, peaks, peak_type = 'peak-uncalled', marker='undefined'):
        """ reset the peaks for this channel, create a new alleleset and
            populate with the peaks with the estimated size and value
        """

        method_id = EK._id('allele-unknown')
        marker_id = Marker.search(marker).id
        type_id = EK._id(peak_type)

        self.reset_peaks()

        alleleset = AlleleSet( sample = self.assay.sample, revision_no = 0 )
        alleleset.method_id = method_id
        self.allelesets.append( alleleset )
        
        alleleset.assign_peaks( peaks, method_id, marker_id, type_id )


    def assign_complete_peaks(self, peaks, method='allele-autoladder'):
        """ reset the peaks for this channel, create a new alleleset and
            populate with the peaks with type and marker
            peaks: [ (value, size, peak, height, area, peak_type, peak_marker, peak_method) ...]
        """

        self.reset_peaks()

        alleleset = AlleleSet( sample = self.assay.sample, revision_no = 0 )
        alleleset.method_id = EK._id(method)
        self.allelesets.append( alleleset )

        alleleset.assign_peaks_with_types( peaks )


    def peaks(self):
        raise NotImplementedError('Who access this method anyway?')
        peak_points = []
        for allele in self.alleles:
            peak_points.append( allele.peak )
        peak_points.sort()
        return peak_points


    def get_latest_alleleset(self):
        return self.allelesets[-1]


    def get_latest_alleles(self):
        return self.get_latest_alleleset().alleles
    alleles = property(get_latest_alleles)


    def reset(self):
        """ remove all allelesets from this channel
        """
        for alleleset in self.allelesets:
            dbsession.delete( alleleset )
        dbsession.flush()


    def scan_peaks(self, parameter=None):
        """ scan peaks on this channel and assign as peak-scanned
        """

        from msaf.lib.fatools import fautils

        alleleset = AlleleSet( sample = self.assay.sample, marker = self.marker,
                                revision_no = 0 )

        alleleset.method = 'allele-unknown'
        self.allelesets.append( alleleset )

        alleles = fautils.scan_peaks( self, parameter=parameter )
        for allele in alleles:
            alleleset.alleles.append( allele )

        return alleleset


    def scan_ladder_peaks(self, ladders, parameter=None):
        """ scan ladder peaks
            ladders: [ 200, 300, 400, ... ]
            return: (z, rss, score, report)
        """

        from msaf.lib.fatools import fautils

        alleleset = AlleleSet( sample = self.assay.sample, marker_id = self.marker_id,
                                revision_no = 0 )
        alleleset.method = 'allele-unknown'
        self.allelesets.append( alleleset )

        return fautils.scan_ladder_peaks( self, ladders, parameter )


    def call_peaks(self, method, ladders, parameter):
        
        from msaf.lib.fatools import fautils

        return fautils.call_peaks( self.alleles, method, ladders, parameter )


    def bin_peaks(self):

        from msaf.lib.fatools import fautils

        fautils.bin_peaks( self, self.marker )


    def get_allele_class(self):
        return Allele


    def set_marker(self, marker):
        for alleleset in self.allelesets:
            alleleset.marker = marker
        self.marker = marker


@registered
class ChannelStringData(StringDataMixIn, Base):
    """ SampleStringData

        This class holds categorical string data from corresponding channel.
    """
    __tablename__ = 'channelstrings'

    channel_id = Column(types.Integer, ForeignKey('channels.id', ondelete='CASCADE'),
                        nullable=False)
    channel = relationship(Channel, uselist=False,
            backref=backref('strings', lazy='dynamic', passive_deletes=True))



# dataset_table manages relationship between dataset and alleleset
dataset_table = Table('datasets_allelesets', metadata,
    Column('id', types.Integer, Sequence('datasets_alleleset_seqid', optional=True),
        primary_key=True),
    Column('dataset_id', types.Integer, ForeignKey('datasets.id'), nullable=False),
    Column('alleleset_id', types.Integer, ForeignKey('allelesets.id'), nullable=False),
    UniqueConstraint( 'dataset_id', 'alleleset_id' ))

dataset_batch_table = Table('datasets_batches', metadata,
    Column('id', types.Integer, Sequence('datasets_batches_seqid', optional=True),
        primary_key=True),
    Column('dataset_id', types.Integer, ForeignKey('datasets.id'), nullable=False),
    Column('batch_id', types.Integer, ForeignKey('batches.id'), nullable=False),
    UniqueConstraint( 'dataset_id', 'batch_id' ))


@registered
class DataSet( BaseMixIn, Base ):
    """ DataSet

        DataSet basically performs versioning (snapshot-ing) on a set of allelesets
        by capturing the allele values on spesific samples at a specific time. Although
        optional, it is recommended that a snapshot be associated with a batch to ease
        the data management and versioning.

    """
    __tablename__ = 'datasets'

    uid = Column(types.String(8), nullable=False, unique=True)
    """ universal, stable 8-bytes string-based ID for this dataset """

    group_id = Column(types.Integer, ForeignKey('groups.id'), nullable=False)
    group = relationship(Group, uselist=False)
    """ primary group where this dataset belongs """

    acl = Column(types.Integer, nullable=False, default=0)
    """ access control list for this dataset """

    previous_id = Column(types.Integer, ForeignKey('datasets.id'), nullable=True)
    """ previous dataset """

    number = Column(types.Integer, nullable=False, default=1)
    """ order no of this dataset """

    latest = Column(types.Boolean, nullable=False, default=False)
    """ is this the latest dataset for this chain of set? """

    public = Column(types.Boolean, nullable=False, default=False)
    """ whether this dataset is publicly available """

    count = Column( types.Integer, nullable=False )
    """ how many allelesets within this dataset """

    desc = deferred( Column(types.Text(), nullable=False, default='') )
    """ any description for this dataset """

    remark = deferred( Column(types.Text(), nullable=False, default='') )
    """ any notes or remark for this dataset """

# dbversion_snapshot_table manages relationship between dbversion and snapshot
dbversion_dataset_table = Table('dbversions_datasets', metadata,
    Column('id', types.Integer, Sequence('dbversions_datasets_seqid', optional=True),
        primary_key=True),
    Column('dbversion_id', types.Integer, ForeignKey('dbversions.id'), nullable=False),
    Column('dataset_id', types.Integer, ForeignKey('datasets.id'), nullable=False),
    UniqueConstraint( 'dbversion_id', 'dataset_id' ))


@registered
class DBVersion( BaseMixIn, Base ):
    """ DBVersion

        DBVersion performs database versioning on a set of snapshots. Only the DBA
        or MasterData can create and manage a database version
    """

    __tablename__ = 'dbversions'

    uid = Column( types.String(8), nullable=False, unique=True )
    """ universal, stable 8-bytes string-bbased ID for this database version """

    label = Column( types.String(64), nullable=False, unique=True )
    """ version label """

    desc = Column( types.String(256), nullable=False, default='' )
    """ simple description of this label """


@registered
class AlleleSet(BaseMixIn, Base):
    """ AlleleSet

        This class holds information about marker and channel results
    """
    __tablename__ = 'allelesets'

    channel_id = Column(types.Integer, ForeignKey('channels.id', ondelete='CASCADE'),
                    nullable=False)
    channel = relationship(Channel, uselist=False,
                backref=backref('allelesets', lazy='dynamic', passive_deletes=True))
    # a channel can have several allele set for different revision numbers

    sample_id = Column(types.Integer, ForeignKey('samples.id', ondelete='CASCADE'),
                    nullable=False)
    sample = relationship(Sample, uselist=False,
                backref=backref('alleleset', lazy='dynamic', passive_deletes=True))
    """ link to sample """

    marker_id = Column(types.Integer, ForeignKey('markers.id'), nullable=False)
    marker = relationship(Marker, uselist=False,
                    backref=backref('allelesets', lazy='dynamic'))
    """ link to marker """

    method_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    method = EK.proxy('method_id')
    """ method for size determination of this marker under EK @ALLELE-METHOD """

    revision_no = Column(types.Integer, nullable=False, default=0)
    """ revision number of this alleleset """

    latest = Column(types.Boolean, nullable=False, default=False)
    """ whether this is the latest revision or not """

    final = Column(types.Boolean, nullable=False, default=False)
    """ whether this alleleset has been finalized """

    shared = Column(types.Boolean, nullable=False, default=False)
    """ whether this alleleset is shared for all users """

    note = deferred(Column(types.Text(), nullable=False, default=''))

    __table_args__ = (  UniqueConstraint( 'channel_id', 'revision_no' ),
                        {} )

    def finalized(self):
        """ the alleles have been finalized """
        self.final = True


    def set_latest(self, flag=True):
        """ set this AlleleSet to be the latest for this particular sample """
        
        # check whether there are other 'latest' AlleleSet from this channel_id
        q = AlleleSet.query().filter( AlleleSet.channel_id == self.channel_id,
                AlleleSet.latest == True )
        for r in q:
            r.latest = False

        # check whether there are other 'latest' AlleleSet containing same marker

        self.latest = flag


    def assign_peaks( self, peaks, method_id, marker_id, type_id ):

        peak_noise_id = EK._id('peak-noise')

        for (v, s, p, h, a) in peaks:
            actual_type_id = type_id if v > 0 else peak_noise_id
            self.alleles.append(
                Allele( value = v, size = float(s), peak = float(p),
                        height = float(h), area = int(a),
                        method_id = method_id, marker_id = marker_id,
                        type_id = actual_type_id )
                )


    def assign_peaks_with_types( self, peaks ):
        """ peaks: [ (values, size, peak, height, area, type, marker, method), ... ]
        """
    
        for (v, s, p, h, a, t, c, m) in peaks:
            self.alleles.append(
                Allele( value = v, size = float(s), rtime = float(p),
                        height = float(h), area = int(a),
                        method_id = EK._id(m), marker_id = Marker.search(c).id,
                        type_id = EK._id(t) )
                )


@registered
class Allele(BaseMixIn, Base):
    """ Allele

        This class holds peaks/alleles for a particular channel.
        Design consideration:
            - there can be no similar value for a given alleleset
            - value is float, so allele such as 232.1 (232 + 1 base) is possible
    """
    __tablename__ = 'alleles'

    alleleset_id = Column(types.Integer, ForeignKey('allelesets.id', ondelete='CASCADE'),
                    nullable=False)
    alleleset = relationship(AlleleSet, uselist=False,
                    backref=backref('alleles', cascade='all, delete-orphan',
                                passive_deletes=True))

    value = Column(types.Float, nullable=False, default=-1)
    """ calculated bin size """

    delta = Column(types.Float, nullable=False, default=-1)
    """ deviation of value to size """
    
    size = Column(types.Float, nullable=False, default=-1)
    """ size of peak/allele after calibrated with controls """
    
    rtime = Column(types.Integer, nullable=False, default=-1)
    """ retention time, real/actual peak coordinat """

    brtime = Column(types.Integer, nullable=False, default=-1)
    ertime = Column(types.Integer, nullable=False, default=-1)
    wrtime = Column(types.Integer, nullable=False, default=-1)
    srtime = Column(types.Float, nullable=False, default=-1)
    """ begin, end, width and symmetrical retention time of this peak """

    
    height = Column(types.Integer, nullable=False, default=-1)
    """ height of signal (rfu) """
    
    area = Column(types.Integer, nullable=False, default=-1)
    """ area of signal """

    beta = Column(types.Float, nullable=False, default=-1)
    """ ratio of peak area / peak height """

    type_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    type = EK.proxy('type_id')
    """ type of this particular allele, under EK key '@PEAK-TYPE',
        eg. 'peak-bin', 'peak-noise', etc """

    method_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    method = EK.proxy('method_id')
    """ binning method of this peak """

    #__table_args__ = (  UniqueConstraint( 'alleleset_id', 'value', 'type_id' ), {} )


    def as_dict(self):
        return dict( value = self.value, size = self.size,
                    rtime = self.rtime, brtime = self.brtime, ertime = self.ertime,
                    height = self.height, area = self.area )

    def __repr__(self):
        return ('<Allele [% 3d] rtime [% 5d] height [% 5d] area [%d]>' %
                        (self.value or -1, self.rtime, self.height, self.area ))

    def update(self, obj):
        if obj.value is not None:
            self.value = obj.value
        if obj.delta is not None:
            self.delta = obj.delta
        if obj.size is not None:
            self.size = obj.size
        if obj.rtime is not None:
            self.rtime = obj.rtime
        if obj.brtime is not None:
            self.brtime = obj.brtime
        if obj.ertime is not None:
            self.ertime = obj.ertime
        if obj.height is not None:
            self.height = obj.height
        if obj.area is not None:
            self.area = obj.area
        if obj.type_id is not None:
            self.type_id = obj.type_id
        if obj.method_id is not None:
            self.method_id = obj.method_id




