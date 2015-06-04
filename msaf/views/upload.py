import logging

log = logging.getLogger(__name__)

from pyramid.response import Response
from pyramid.renderers import render_to_response

from rhombus.lib.roles import PUBLIC
from rhombus.views import roles
from rhombus.views.errors import error_page, not_authorized
from msaf.configs import get_temp_path
from rhombus.lib.utils import random_string
#from msaf.lib.dictfmt import csv2json, json2db, json2db2
from msaf.lib import dictfmt as msaf_dictfmt
import json, yaml, transaction
from io import StringIO
import os

# XXX: todo - refactor to use POST/REDIRECT/GET processing pattern
# GET /upload/index
# POST /upload/verify - REDIRECT - GET /upload/verify (Verify page)
# POST /upload/commit - REDIRECT - GET /upload/commit (Success page)
# GET /


@roles( PUBLIC )
def index(request):

    return render_to_response( "msaf:templates/upload/index.mako", {}, 
            request = request )


@roles( PUBLIC )
def verify(request, dictfmt = msaf_dictfmt):
    # perform consistency check, sanity check
    # dictfmt -> module for dictionary format functions

    if not request.POST:
        return Response("ERROR: not a valid operation [upload:100]")        

    input_file = request.POST.get('input_file', None)
    #opt_replace_existing = request.POST.get('replace_existing', None)

    name, ext = os.path.splitext( input_file.filename )

    if ext in [ '.csv', '.tab', '.tsv' ]:
        # convert to JSON first
        # consistency checks
        if ext == '.csv':
            delim = ','
        else:
            delim = '\t'

        try:
            dict_samples, report_log = dictfmt.csv2dict(
                            StringIO(input_file.file.read().decode('UTF-8')),
                            with_report=True,
                            delimiter = delim )
        except ValueError as err:
            return error_page( 'ValueError: {0}'.format(err) )
        if dict_samples is None:
            return render_to_response( "msaf:templates/upload/error.mako",
                { 'report_log': report_log.getvalue() }, request = request )

        dict_text = yaml.dump( dict_samples )
        ext = '.yaml'

    elif ext in ['.json', '.yaml']:
        dict_text = input_file.file.read().decode('UTF-8')
        report_log = StringIO()

    else:

        return error_page('Unrecognized format')

    # sanity check
    # data integrity check (flush to database, but no commit yet)

    temppath = get_temp_path( random_string(8) + ext )
    with open(temppath, 'w') as f:
        f.write( dict_text )

    ticket = request.get_ticket( { 'dict.path': temppath } )
    #                'replace_allele': opt_replace_existing } )

    return render_to_response( "msaf:templates/upload/verify.mako",
            { 'report_log': report_log.getvalue(), 'ticket': ticket,
                'filename': input_file.filename },
            request = request )



@roles( PUBLIC )
def commit(request):
    # commit the data to database
    if not request.POST:
        return Response('ERROR: not a valid operation [upload:200]')

    ticket = request.POST.get('ticket', None)
    if not ticket:
        return Response('ERROR: not a valid operation [upload:210]')

    p = request.get_data( ticket )
    if 'dict.path' not in p:
        return Response('ERROR: not a valid operation [upload:220]')

    dict_f = open( p['dict.path'] )

    if request.POST.get('_method', None) == 'view_json':
        return Response( json.dumps( json.load(json_f), indent=2 ),
                    content_type = 'text/json' )

    if request.POST.get('_method', None) == 'commit':
        batch_code = request.POST.get('batch_code', None)
        desc = request.POST.get('desc', '')
        group_id = request.POST.get('group', 0)
        assay_provider_id = request.POST.get('assay_provider', 0)
        update_sample = request.POST.get('opt_update_sample', False)
        update_allele = request.POST.get('opt_update_allele', False)
        with transaction.manager:
            json2db(json_f, batch_code=batch_code, desc=desc, group_id = group_id, assay_provider_id = assay_provider_id)

    return render_to_response( "msaf:templates/upload/commit.mako",
        { 'report_log': None }, request=request )






