import logging

from pyramid.response import Response
from pyramid.renderers import render_to_response
from pyramid.httpexceptions import HTTPFound

log = logging.getLogger(__name__)

from rhombus.models.user import UserClass
from rhombus.views.errors import error_page

def index(request):
    return render_to_response( "msaf:templates/home.mako", {}, request=request )


def login(request):

    if request.POST:
        login = request.POST.get('username', '')
        passwd = request.POST.get('password', '')

        userclass = UserClass.get( 1 )

        userinstance = userclass.auth_user( login, passwd )

        if userinstance is None:
            request.session.flash( ('error', 'ALERT: Wrong username or password.') )
        else:

            request.session['user'] = userinstance
            request.session.flash( ('info', 'You have been authenticated as: %s' % userinstance.login ) )

    return HTTPFound(location='/')


def logout(request):
    
    if request.session.has_key('user'):
        del request.session['user']
        request.session.flash( ('info', 'You have been logged out') )

    return HTTPFound(location='/')


def not_implemented(request):

    return error_page('This function has not been implemented. Please contact the developer for more info.')


