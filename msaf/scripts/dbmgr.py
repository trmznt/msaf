
import sys, os, io
import argparse, transaction
import yaml, json

from msaf.models import Panel, Marker, EK, dbsession


def init_argparser():

    parser = argparse.ArgumentParser( '' )

    parser.add_argument('--exportpanel', required=False, default=False,
            help = 'exporting panel from database')
    parser.add_argument('--importpanel', required=False, default=False,
            help = 'importing panel from yaml file')

    parser.add_argument('--exportmarker', required=False, default=False,
            help = 'exporting marker from database')
    parser.add_argument('--importmarker', required=False, default=False,
            help = 'importing marker to database')

    parser.add_argument('--outfile', required=False, default=None,
            help = 'filename output')
    parser.add_argument('--commit', required=False, action='store_true', default=False,
            help = 'commit to database')
    parser.add_argument('--update', required=False, action='store_true', default=False,
            help = 'perform update if entity is already in database')

    parser.add_argument('--name', required=False, default='',
            help = 'panel name, comma separated')

    return parser


def main(args):

    if args.commit:
        with transaction.manager:
            do_dbmgr(args)
    else:
        do_dbmgr(args)


def do_dbmgr(args):

    if args.exportpanel is not False:
        do_exportpanel(args)
    elif args.importpanel is not False:
        do_importpanel(args)
    elif args.exportmarker is not False:
        do_exportmarker(args)
    elif args.importmarker is not False:
        do_importmarker(args)
    else:
        print('Do nothing?')



def do_exportek(args):

    print('Exporting EnumKeys')

    panels = args.exportpanel.split(',')

    panel_dicts = {}

    for panel_name in panels:
        ek = EK.search(panel_name)
        panel_dicts[ek.key] = dict( key=ek.key,
                                    desc=ek.desc,
                                    data=ek.data_from_json() )

    with open(args.outfile, 'w') as f:
        f.write( yaml.dump( panel_dicts ) )


def do_importek(args):

    print('Importing EnumKeys')

    with open(args.importpanel) as f:
        panel_dicts = yaml.load( f )

    names = []
    if args.name:
        names = args.name.lower().split(',')

    for (panel_name, panel) in panel_dicts.items():
        if names and panel_name.lower() not in names:
            continue
        if panel_name != panel['key']:
            raise RuntimeError('inconsistent panel key: %s' % panel_name)

        ek_panel = EK.search('@PANEL')
        ek = EK( key=panel['key'], desc=panel['desc'],
                 data = json.dumps(panel['data']).encode('UTF-8'),
                 member_of_id = ek_panel.id )
        dbsession.add( ek )
        dbsession.flush()
        print('Importing %s' % panel_name)

    print('Done!')


def do_importpanel(args):

    print('Importing panels')

    with open(args.importpanel) as f:
        panel_dicts = yaml.load( f )

    names = []
    if args.name:
        names = args.name.lower().split(',')

    for (panel_name, panel_data) in panel_dicts.items():
        if names and panel_name.lower() not in names:
            continue
        print( panel_data )

        # the following codes perform sanity checking

        if panel_name != panel_data['code']:
            raise RuntimeError('inconsistent panel key: %s' % panel_name)

        marker_data = panel_data['data']['markers']
        for marker_name in marker_data:
            marker_code = Marker.search(marker_name)
            if marker_code is None:
                raise RuntimeError('Unknown marker name: %s' % marker_code)
            dye_code = marker_data[marker_name]['dye']
            dye = EK.search(dye_code)
            if dye is None:
                raise RuntimeError('Unknown dye name: %s' % dye_code)

        panel = Panel.from_dict(panel_data, update=args.update)
        print('Importing %s' % panel.code)

    print('Done!')


def do_exportpanel(args):

    print('Exporting panels')

    panel_names = args.exportpanel.split(',')

    panel_dicts = {}

    for panel_name in panel_names:
        panel = Panel.search(panel_name)
        panel_dicts[panel.code] = panel.as_dict()

    with open(args.outfile, 'w') as f:
        f.write( yaml.dump( panel_dicts ) )


def do_exportmarker(args):

    print('Exporting marker')

    marker_names = args.exportmarker.split(',')

    marker_dicts = {}

    for marker_name in marker_names:
        marker = Marker.search(marker_name)
        marker_dicts[marker.code] = marker.as_dict()

    with open(args.outfile, 'w') as f:
        f.write( yaml.dump( marker_dicts ) )



def do_importmarker(args):

    print('Importing marker(s)')

    with open(args.importmarker) as f:
        marker_dicts = yaml.load( f )

    names = []
    if args.name:
        names = args.name.lower().split(',')

    for (marker_name, marker_data) in marker_dicts.items():
        if names and marker_name.lower() not in names:
            continue
        print( marker_data )
        if marker_name != marker_data['code']:
            raise RuntimeError('inconsistent marker code: %s' % marker_name)

        marker = Marker.from_dict( marker_data, args.update )

        
        print('Importing %s' % marker.code)

    print('Done!')


