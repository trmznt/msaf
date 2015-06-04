from pyramid.config import Configurator
from pyramid.events import BeforeRender

from sqlalchemy import engine_from_config

from rhombus import config_app, rhombus_config, add_route_view
from msaf.models import init_db as msaf_init_db
from msaf.configs import set_temp_path, set_proc_path, set_libexec_path
from msaf.lib.procmgmt import init_pool

import msaf.lib.helpers as h

import os

console_mode = False

def run_console( func ):
    global console_mode
    console_mode = True
    return func()

def msaf_init(settings):
    global console_mode

    # preparing directories (in future, this should be in msaf_init())
    temp_path = settings['msaf.temp_directory']
    if not os.path.exists( temp_path ):
        os.makedirs( temp_path )
    set_temp_path( temp_path )

    proc_path = settings['msaf.proc_directory']
    if not os.path.exists( proc_path ):
        os.makedirs( proc_path )
    set_proc_path( proc_path )

    libexec_path = settings['msaf.libexec_directory']
    if not os.path.exists( libexec_path ):
        os.makedirs( libexec_path )
    set_libexec_path( libexec_path )

    if not console_mode:
        init_pool()


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    msaf_init(settings)

    config = config_app(global_config, settings, msaf_init_db)
    config.add_static_view('static', 'msaf:static/', cache_max_age=3600)
    #config.add_static_view('rhombus-static', 'rhombus:static/', cache_max_age=3600)

    # home
    config.add_route('home', '/')
    config.add_view('msaf.views.home.index', route_name='home')

    # login/logout
    config.add_route('login', '/login')
    config.add_view('msaf.views.home.login', route_name='login')
    config.add_route('logout', '/logout')
    config.add_view('msaf.views.home.logout', route_name='logout')

    rhombus_config( config, '/mgr' )
    msaf_config( config )
    #config.scan()


    return config.make_wsgi_app()


def module_for_view( view_name, default_module, module_map ):
    if view_name in module_map:
        return module_map[view_name]
    return default_module

def msaf_config( config, prefix='', default_module='msaf', module_map = {} ):
    
    config.add_route('explore', '/explore')
    config.add_view('msaf.views.explore.index', route_name='explore')


    module_name = module_for_view('marker', default_module, module_map)
    add_route_view( config, module_name, '%s.views.marker' % module_name, prefix,
        ('marker', '/marker'),
        ('marker-action', '/marker/@@action'),
        ('marker-edit', '/marker/{id}@@edit'),
        ('marker-save', '/marker/{id}@@save'),
        ('marker-view', '/marker/{id}', 'view')
    )

    add_route_view( config, 'msaf', 'msaf.views.batch', prefix,
        ('batch', '/batch'),
        ('batch-action', '/batch/@@action'),
        ('batch-edit', '/batch/{id}@@edit'),
        ('batch-save', '/batch/{id}@@save'),
        ('batch-view', '/batch/{id}', 'view')
    )

    module_name = module_for_view('location', default_module, module_map)
    add_route_view( config, module_name, '%s.views.location' % module_name, prefix,
        ('location', '/location'),
        ('location-action', '/location/@@action'),
        ('location-lookup', '/location/@@lookup', 'lookup', 'json'),
        ('location-edit', '/location/{id}@@edit'),
        ('location-save', '/location/{id}@@save'),
        ('location-view', '/location/{id}', 'view')
    )

    module_name = module_for_view('sample', default_module, module_map)
    add_route_view( config, module_name, '%s.views.sample' % module_name, prefix,
        ('sample', '/sample'),
        ('sample-action', '/sample/@@action'),
        ('sample-edit', '/sample/{id}@@edit'),
        ('sample-save', '/sample/{id}@@save'),
        ('sample-view', '/sample/{id}', 'view'),
    )

    add_route_view( config, 'msaf', 'msaf.views.assay', prefix,
        ('assay', '/assay'),
        ('assay-action', '/assay/@@action'),
        ('assay-edit', '/assay/{id}@@edit'),
        ('assay-save', '/assay/{id}@@save'),
        ('assay-drawchannels', '/assay/{id}@@drawchannels'),
        ('assay-view', '/assay/{id}', 'view'),
    )

    add_route_view( config, 'msaf', 'msaf.views.channel', prefix,
        ('channel', '/channel'),
        ('channel-action', '/channel/@@action'),
        ('channel-edit', '/channel/{id}@@edit'),
        ('channel-save', '/channel/{id}@@save'),
        ('channel-view', '/channel/{id}', 'view'),
    )


    config.add_route('not-implemented', '/not_implemented')
    config.add_view('msaf.views.home.not_implemented', route_name='not-implemented')

    config.add_route('upload', '/upload')
    config.add_view('msaf.views.upload.index', route_name='upload')

    config.add_route('upload-verify', '/upload/verify')
    config.add_view('msaf.views.upload.verify', route_name='upload-verify')

    config.add_route('upload-commit', '/upload/commit')
    config.add_view('msaf.views.upload.commit', route_name='upload-commit')

    config.add_route('queryset', '/queryset')
    config.add_view('msaf.views.queryset.index', route_name='queryset')

    config.add_route('analysis-allele', '/analysis/allele')
    config.add_view('msaf.views.analysis.allele.index', route_name='analysis-allele')

    config.add_route('analysis-moi', '/analysis/moi')
    config.add_view('msaf.views.analysis.moi.index', route_name='analysis-moi')

    config.add_route('tools-moi', '/tools/moi')
    config.add_view('msaf.views.tools.moi.index', route_name='tools-moi')

    config.add_route('tools-he', '/tools/he')
    config.add_view('msaf.views.tools.he.index', route_name='tools-he')

    config.add_route('tools-genotype', '/tools/genotype')
    config.add_view('msaf.views.tools.genotype.index', route_name='tools-genotype')

    config.add_route('tools-haplotype', '/tools/haplotype')
    config.add_view('msaf.views.tools.haplotype.index', route_name='tools-haplotype')

    config.add_route('tools-allele', '/tools/allele')
    config.add_view('msaf.views.tools.allele.index', route_name='tools-allele')

    config.add_route('analysis-predefined', '/analysis/predefined')
    config.add_view('msaf.views.analysis.predefined.index', route_name='analysis-predefined')

    config.add_route('tools-report', '/tools/report')
    config.add_view('msaf.views.tools.report.index', route_name='tools-report')

    config.add_route('tools-export', '/tools/export')
    config.add_view('msaf.views.tools.export.index', route_name='tools-export')

    config.add_route('tools-lian', '/tools/lian')
    config.add_view('msaf.views.tools.lian.index', route_name='tools-lian')

    config.add_route('tools-pca', '/tools/pca')
    config.add_view('msaf.views.tools.pca.index', route_name='tools-pca')

    config.add_route('tools-nj', '/tools/nj')
    config.add_view('msaf.views.tools.nj.index', route_name='tools-nj')

    config.add_route('tools-structure', '/tools/structure')
    config.add_view('msaf.views.tools.structure.index', route_name='tools-structure')

    config.add_subscriber( add_global, BeforeRender )
    #config.set_renderer_globals_factory( lambda x: { 'h': h } )


def add_global(event):
    event['h'] = h

