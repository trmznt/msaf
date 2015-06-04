
import os
import sys
import transaction

from sqlalchemy import engine_from_config

from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from vivaxdi.models import init_db

from vivaxdi.lib.jsonfmt import json2db


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> <json_file>\n'
          '(example: "%s development.ini infile.json")' % (cmd, cmd)) 
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) != 3:
        usage(argv)

    config_uri = argv[1]
    infile = open(argv[2])

    print "setup logging"
    setup_logging(config_uri)

    print "get appsetings"
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')

    print "initialize db"
    init_db( engine )

    # insert cvs file
    with transaction.manager:
        json2db( infile )


if __name__ == '__main__':
    main()
