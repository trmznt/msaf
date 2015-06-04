import sys, os
import transaction

from sqlalchemy import engine_from_config

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from rhombus.models.user import UserClass, Group
from rhombus.models.ek import EK
from rhombus.lib.roles import *

from msaf import run_console
from msaf.models import init_db
from msaf.models.setup import setup_db
from msaf.models.msdb import Marker


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd)) 
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]

    print("preparing directories")
    for dirname in [ 'db', 'temp', 'proc' ]:
        if not os.path.exists(dirname):
            os.mkdir(dirname)

    print("setup logging")
    setup_logging(config_uri)

    print("get appsettings")
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    
    # inititalize db and create all tables
    init_db( engine, create_table = True )

    setup_db()

    with transaction.manager:
        populate_db()


def populate_db():

    # add new domain/user class
    Group.bulk_insert( init_groups )
    UserClass.bulk_insert( init_userclass )
    EK.bulk_insert( ek_genotype )
    Marker.bulk_insert( markers )


init_groups = [ ( 'Group#1', [ PUBLIC ] ),
                ( 'Group#2', [ PUBLIC ] ) ]

init_userclass = ( 'DOM#1', 'Domain of domain.dom', None,
                        {   'sys': 'LDAP', 'DN': 'uid=%s,ou=Users,dc=domain,dc=dom',
                            'host': 'master.eijkman.go.id' },
    [ 
        ( 'user1', 'LastName1', 'FirstName1', 'user1@domain.dom', 'abcde',
            [ '_SysAdm_', 'Group#1', 'Group#2' ]),
        ( 'demo_user', 'User', 'Demo', 'demo_user@domain.dom', 'demo_PassWD',
            [ ] )
    ] )

#( code, gene, primer_fwd, primer_rev, nested, related_to, desc, repeats, min, max, species )

locations = { 'undefined':
                dict( adminl1='-', adminl2='-', adminl3='-', adminl4='-' )
            }

markers = [ ('undefined', '-', '-', '-', False, None, None, 0, 0, 0, 'X'),
            ]


if __name__ == '__main__':
    run_console(main)
