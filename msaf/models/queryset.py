
from rhombus.models.core import *
from rhombus.models.filemgr import *
from rhombus.models.user import *
from msaf.models.msdb import Sample


queried_samples = Table( 'queried_samples', Base.metadata,
    Column('queryset_id', types.Integer, ForeignKey('querysets.id')),
    Column('sample_id', types.Integer, ForeignKey('samples.id')),
    UniqueConstraint ('queryset_id', 'sample_id')
)


@registered
class QuerySet( BaseMixIn, Base ):

    __tablename__ = 'querysets'

    group_id = Column(types.Integer, ForeignKey('groups.id'), default=get_groupid,
            nullable=False)
    group = relationship(Group, uselist=False)
    """ primary group where this user's belongs """

    acl = Column(types.Integer, nullable=False, default=0)
    """ access control list for this queryset """


    desc = deferred( Column(types.Text(), nullable=False, default='') )
    count = Column(types.Integer, nullable=False)
    query_text = Column(types.Text(), nullable=False)

    samples = relationship(Sample, secondary=queried_samples, lazy='dynamic',
                backref=backref('querysets'))


@registered
class Process( Base ):

    __tablename__ = 'processes'

    id = Column(types.Integer, Sequence('process_seqid', optional=True),
            primary_key=True)
    user_id = Column(types.Integer, ForeignKey('users.id'), default=get_userid,
            nullable=False)
    stamp = Column(types.TIMESTAMP, nullable=False, default=current_timestamp())

    status = Column(types.String(1), nullable=False, default='I')
    start_time = Column(types.TIMESTAMP)
    end_time = Column(types.TIMESTAMP)
    pid = Column(types.Integer, nullable=False)
    yamldata = deferred(Column(YAMLCol()))
    msg = deferred(Column(types.Text()))
