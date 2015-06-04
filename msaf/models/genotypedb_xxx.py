
from rhombus.models.core import *
from rhombus.models.user import User, Group
from rhombus.models.ck import CK

# create numpy array column
# grr, numpy needs StringIO

import numpy, copy

class NPArray(types.MutableType, types.TypeDecorator):
    impl = types.BLOB

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        #buf = value.tostring()
        buf = StringIO()
        numpy.save(buf, value)
        return buf.getvalue()

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        buf = StringIO(value)
        return numpy.load(buf)
        #return numpy.fromstring(value)

    def copy_value(self, value):
        return copy.deepcopy( value )


@registered
class Location(Base):
    """ regions """
    __tablename__ = 'locations'
    id = Column(types.Integer, Sequence('location_seqid', optional=True),
            primary_key=True)
    lastuser_id = Column(types.Integer, ForeignKey('users.id'),
            default=get_userid, onupdate=get_userid,
            nullable=False)
    stamp = Column(types.TIMESTAMP, nullable=False, default=current_timestamp())

    country_id = Column(types.Integer, ForeignKey('cks.id'), nullable=False)
    state_id = Column(types.Integer, ForeignKey('cks.id'), nullable=False)
    region_id = Column(types.Integer, ForeignKey('cks.id'), nullable=False)
    town_id = Column(types.Integer, ForeignKey('cks.id'), nullable=False)

    country = CK.proxy('country_id', '@REGION')
    state = CK.proxy('state_id', '@REGION')
    region = CK.proxy('region_id', '@REGION')
    town = CK.proxy('town_id', '@REGION')

    latitude = Column(types.Float)
    longitude = Column(types.Float)

    __table_args__ = ( UniqueConstraint('country_id', 'state_id', 'region_id', 'town_id'), {} )

    @staticmethod
    def search(country, state, region, town, auto=False):
        country_id = CK._id(country, '@REGION', auto)
        state_id = CK._id(state, '@REGION', auto)
        region_id = CK._id(region, '@REGION', auto)
        town_id = CK._id(town, '@REGION', auto)

        q = Location.query().filter(
                and_(Location.country_id == country_id,
                        Location.state_id == state_id,
                        Location.region_id == region_id,
                        Location.town_id == town_id ) )
        r = q.all()
        if len(r) == 0 and auto:
            location = Location( country_id = country_id,
                                state_id = state_id,
                                region_id = region_id,
                                town_id = town_id )
            dbsession.add( location )
            dbsession.flush()

            return location

        return r[0]

    @staticmethod
    def grep(term):
        regions = CK.get_members('@REGION').filter( CK.key.contains( term.lower() ) )
        ids = [ r.id for r in regions ]
        return Location.query().filter(
            or_( Location.country_id.in_( ids ), Location.state_id.in_( ids ),
                Location.region_id.in_( ids ), Location.town_id.in_( ids ) ) )


    def render(self):
        return "%s / %s / %s / %s" % (self.country, self.state, self.region, self.town )

    def __repr__(self):
        return '<Location: %s>' % self.render()

    def sample_count(self):
        return self.samples.count()

        
                        

@registered
class Subject(Base):
    """ subjects """
    __tablename__ = 'subjects'
    id = Column(types.Integer, Sequence('subject_seqid', optional=True),
            primary_key=True)
    lastuser_id = Column(types.Integer, ForeignKey('users.id'),
            default=get_userid, onupdate=get_userid,
            nullable=False)
    stamp = Column(types.TIMESTAMP, nullable=False, default=current_timestamp())

    name = Column(types.String(64), unique=True, nullable=False)
    yearofbirth = Column(types.Integer, nullable=False)
    gender = Column(types.String(1), nullable=False)
    notes = deferred( Column(types.Text()) )

    __table_args__ = ( UniqueConstraint( 'name', 'gender', 'yearofbirth' ), {} )

    @staticmethod
    def search( name, gender, yearofbirth, auto=False ):
        q = Subject.query().filter( and_( Subject.name == name, Subject.gender == gender,
                Subject.yearofbirth == yearofbirth ) )
        r = q.all()
        if len(r) == 0:
            if auto:
                subject = Subject( name = name, gender = gender, yearofbirth = yearofbirth )
                dbsession.add( subject )
                #dbsession.flush()
                return subject
            return None
        return r[0]


@registered
class Batch(Base):
    """ batches """
    __tablename__ = 'batches'
    id = Column(types.Integer, Sequence('sample_seqid', optional=True),
            primary_key=True)
    lastuser_id = Column(types.Integer, ForeignKey('users.id'),
            default=get_userid, onupdate=get_userid,
            nullable=False)
    stamp = Column(types.TIMESTAMP, nullable=False, default=current_timestamp())

    published = Column(types.Boolean, nullable=False, default=False)
    shared = Column(types.Boolean, nullable=False, default=False)
    status = Column(types.String(1), nullable=False, default='U')
    # U - upload file, D - direct creation, S - in submission, R - in review
    code = Column(types.String(32), nullable=False)
    desc = deferred(Column(types.Text()))
    group_id = Column(types.Integer, ForeignKey('groups.id'), nullable=False)

    group = relationship(Group, uselist=False)
    lastuser = relationship(User, uselist=False)

    def __repr__(self):
        return '<Group: %s>' % self.code

    def publish(self):
        for s in self.samples:
            if not s.published:
                s.publish()
        for a in self.assays:
            a.publish()
        self.published = True

    def change_group(self, group, bypass=False):
        self.group_id = group.id

        if bypass:
            # use raw SQL to improve performance instead of using ORM
            Sample.query().filter( Sample.batch_id == self.id ).update( dict(group_id = group.id ) )

        # or use normal ORM procedure
        for s in self.samples:
            s.group_id = group.id



@registered
class Sample(Base):
    """ samples """
    __tablename__ = 'samples'
    id = Column(types.Integer, Sequence('sample_seqid', optional=True),
            primary_key=True)
    lastuser_id = Column(types.Integer, ForeignKey('users.id'),
            default=get_userid, onupdate=get_userid,
            nullable=False)
    stamp = Column(types.TIMESTAMP, nullable=False, default=current_timestamp())

    published = Column(types.Boolean, nullable=False, default=False)
    shared = Column(types.Boolean, nullable=False, default=False)
    name = Column(types.String(16), nullable=False)
    collection_date = Column(types.Date, nullable=False)
    passive_case_detection = Column(types.Boolean)
    type_id = Column(types.Integer, nullable=False, default=1)  # sample or reference
    storage_id =Column(types.Integer, ForeignKey('cks.id'), nullable=False)
    method_id = Column(types.Integer, ForeignKey('cks.id'), nullable=False)
    microscopy_ident = Column(types.String(16))
    pcr_ident = Column(types.String(16))
    pcr_method = Column(types.String(16))
    recurrent = Column(types.Boolean, nullable=False, default=False)
    comments = deferred(Column(types.Text()))
    location_id = Column(types.Integer, ForeignKey('locations.id'), nullable=False)
    subject_id = Column(types.Integer, ForeignKey('subjects.id'),
            nullable=False)

    group_id = Column(types.Integer, ForeignKey('groups.id'), nullable=False)
    batch_id = Column(types.Integer, ForeignKey('batches.id'), nullable=False)

    __table_args__ = ( UniqueConstraint('name', 'location_id'), {} )

    location = relationship(Location, uselist=False, backref=backref('samples', lazy='dynamic'))
    subject = relationship(Subject, uselist=False, backref=backref('samples', lazy='dynamic'))
    batch = relationship(Batch, uselist=False, backref=backref('samples', lazy='dynamic'))

    storage = CK.proxy('storage_id')
    method = CK.proxy('method_id')

    @staticmethod
    def search( subject_id=None, name=None, collection_date=None, location_id=None,
                auto=False ):
        q = Sample.query()
        filters = []
        if subject_id:
            filters.append( Sample.subject_id == subject_id )
        if name:
            filters.append( Sample.name == name )
        if collection_date:
            filters.append( Sample.collection_date == collection_date )
        if location_id:
            filters.append( Sample.location_id == location_id )
        q = q.filter( and_( *filters ) )
        r = q.all()
        if len(r) == 0:
            if auto:
                sample = Sample( subject_id=subject_id, name=name, location_id=location_id,
                        collection_date=collection_date )
                #raise RuntimeError(collection_date)
                dbsession.add( sample )
                return sample
            return None
        if len(r) == 1:
            return r[0]
        return r

    def age(self):
        return self.collection_date.year - self.subject.yearofbirth

    def gender(self):
        return self.subject.gender

    def publish(self):
        self.published = True
        for a in self.assays:
            a.publish()

    def share(self):
        self.shared = True
        for a in self.assays:
            a.share()


@registered
class Assay(Base):
    """ assays """

    __tablename__ = 'assays'
    """ mapper tablename """

    id = Column(types.Integer, Sequence('assay_seqid', optional=True),
            primary_key=True)
    """ object primary key """

    lastuser_id = Column(types.Integer, ForeignKey('users.id'),
            default=get_userid, onupdate=get_userid,
            nullable=False)
    """ last modifiying user """

    stamp = Column(types.TIMESTAMP, nullable=False, default=current_timestamp())
    """ last modified stamp """

    sample_id = Column(types.Integer, ForeignKey('samples.id'), nullable=False)
    """ sample id """

    batch_id = Column(types.Integer, ForeignKey('batches.id'), nullable=False)
    """ batch id """

    filename = Column(types.String(128), nullable=False)
    """ original FSA filename of the assay """

    size_standard_id = Column(types.Integer, ForeignKey('cks.id'), nullable=False)
    """ CK of size standard, under @LADDER """

    panel_id = Column(types.Integer, ForeignKey('cks.id'), nullable=False)
    """ CK of panel, under @PANEL """

    published = Column(types.Boolean, nullable=False, default=False)
    status = Column(types.String(1), nullable=False, default='M')
    notes = deferred(Column(types.Text()))
    rawdata = deferred(Column(types.Binary()))  # fsa content
    z = deferred(Column(NPArray))   # polynomial parameter
    #dilution = Column(types.Integer)

    # fragment-analysis stuff

    sample = relationship(Sample, uselist=False,
            backref=backref('assays', lazy='dynamic'))

    batch = relationship(Batch, uselist=False,
            backref=backref('assays', lazy='dynamic'))

    size_standard = CK.proxy('size_standard_id')
    panel = CK.proxy('panel_id')

    def publish(self):
        self.published = True
        for m in self.markers:
            m.publish()

    def share(self):
        for m in self.markers:
            m.share()


@registered
class MarkerSet(Base):
    """ markersets """
    __tablename__ = 'markersets'
    id = Column(types.Integer, Sequence('markerset_seqid', optional=True),
            primary_key=True)
    lastuser_id = Column(types.Integer, ForeignKey('users.id'),
            default=get_userid, onupdate=get_userid,
            nullable=False)
    stamp = Column(types.TIMESTAMP, nullable=False, default=current_timestamp())

    name = Column(types.String(32), nullable=False, unique=True)
    gene = Column(types.String(32), nullable=False)
    primer_1 = Column(types.String(48), nullable=False)
    primer_2 = Column(types.String(48), nullable=False)
    repeats = Column(types.Integer, nullable=False, default=2)
    nested = Column(types.Boolean, nullable=False)
    desc = Column(types.Text())

    @staticmethod
    def search(marker_name):
        q = MarkerSet.query().filter( MarkerSet.name == marker_name )
        return q.one()

    @staticmethod
    def bulk_insert(markers):
        """ [ (name, gene, primer_1, primer_2, nested, related_to, desc ] """
        for m in markers:
            marker = MarkerSet( name=m[0], gene=m[1], primer_1=m[2], primer_2=m[3],
                    nested=m[4],desc=m[6] )
            if m[5]:
                # perform lookup and get id
                pass
            dbsession.add( marker )

    @staticmethod
    def dump_all():
        """ dump data as JSON """
        pass

    def as_dict(self):
        return dict( name = self.name, gene = self.gene,
                primer_1 = self.primer_1, primer_2 = self.primer_2,
                repeats = self.repeats, nested = self.nested,
                desc = self.desc )

    def sample_count(self):
        return self.markers.count()

    def sample_with_allele_count(self):
        c = 0
        for m in self.markers:
            if len(m.alleles) > 0:
                c += 1
        return c


@registered
class Marker(Base):
    """ markers """
    __tablename__ = 'markers'
    id = Column(types.Integer, Sequence('marker_seqid', optional=True),
            primary_key=True)
    lastuser_id = Column(types.Integer, ForeignKey('users.id'),
            default=get_userid, onupdate=get_userid,
            nullable=False)
    stamp = Column(types.TIMESTAMP, nullable=False, default=current_timestamp())

    markerset_id = Column(types.Integer, ForeignKey('markersets.id'), nullable=False)
    assay_id = Column(types.Integer, ForeignKey('assays.id'), nullable=False)
    sample_id = Column(types.Integer, ForeignKey('samples.id'), nullable=False)
    channel_id = Column(types.Integer, ForeignKey('channels.id'), nullable=False)

    published = Column(types.Boolean, nullable=False, default=False)
    shared = Column(types.Boolean, nullable=False, default=False)
    note = deferred(Column(types.Text()))

    __table_args__ = ( UniqueConstraint( 'markerset_id', 'sample_id', 'assay_id' ),
                       UniqueConstraint( 'assay_id', 'dye' ), {} )

    sample = relationship(Sample, uselist=False,
                backref=backref('markers', order_by='Marker.markerset_id', lazy='dynamic'))
    
    assay = relationship(Assay, uselist=False, backref=backref('markers'))
    markerset = relationship(MarkerSet, uselist=False, backref=backref('markers', lazy='dynamic'))

    def publish(self):
        self.published = True

    def share(self):
        self.shared = True


@registered
class Channel(Base):
    """ channels in assay """
    __tablename__ = 'channels'
    id = Column(types.Integer, Sequence('channel_seqid', optional=True),
            primary_key=True)
    lastuser_id = Column(types.Integer, ForeignKey('users.id'),
            default=get_userid, onupdate=get_userid,
            nullable=False)
    stamp = Column(types.TIMESTAMP, nullable=False, default=current_timestamp())

    assay_id = Column(types.Integer, ForeignKey('assays.id'), nullable=False)
    raw_data = deferred(Column(NPArray, nullable=False))  # raw data
    wavelen = Column(types.Integer, nullable=False)
    data = Column(NPArray, nullable=False)   # savitzky-golay smoothed data

    assay = relationship(Assay, uselist=False, backref=backref('channels', lazy='dynamic'))


@registered
class Allele(Base):
    """ alleles """
    __tablename__ = 'alleles'
    id = Column(types.Integer, Sequence('allele_seqid', optional=True),
            primary_key=True)
    lastuser_id = Column(types.Integer, ForeignKey('users.id'),
            default=get_userid, onupdate=get_userid,
            nullable=False)
    stamp = Column(types.TIMESTAMP, nullable=False, default=current_timestamp())

    markerset_id = Column(types.Integer, ForeignKey('markersets.id'), nullable=False)
    marker_id = Column(types.Integer, ForeignKey('markers.id'), nullable=False)
    sample_id = Column(types.Integer, ForeignKey('samples.id'), nullable=False)
    assay_id = Column(types.Integer, ForeignKey('assays.id'), nullable=False)
    channel_id = Column(types.Integer, ForeignKey('channels.id'))

    value = Column(types.Integer, nullable=False)
    size = Column(types.Float, nullable=False)      # calculated size
    peak = Column(types.Integer, nullable=False)    # peak location
    height = Column(types.Integer, nullable=False)  
    area = Column(types.Integer, nullable=False)
    state = Column(types.Integer, nullable=False, default=1)    # 0 - noise, -1 - stutter

    __table_args__ = ( UniqueConstraint( 'markerset_id', 'sample_id', 'assay_id', 'value' ), {} )

    marker = relationship(Marker, uselist=False, backref=backref('alleles'))
    assay = relationship(Assay, uselist=False, backref=backref('alleles', lazy='dynamix'))
    sample = relationship(Sample, uselist=False, backref=backref('alleles', lazy='dynamic'))
    channel = relationship(Channel, uselist=False, backref=backref('alleles', lazy='dynamic'))
