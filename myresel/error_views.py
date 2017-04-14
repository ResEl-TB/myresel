# pylint: disable=unexpected-keyword-arg
from django.shortcuts import render_to_response
from django.template import RequestContext


# HTTP Error 400
def bad_request(request):
    response = render_to_response('400.html',)

    response.status_code = 400

    return response


# HTTP Error 403
def permission_denied(request):
    response = render_to_response('403.html',)

    response.status_code = 403

    return response


# HTTP Error 404
def page_not_found(request):
    response = render_to_response('404.html',)

    response.status_code = 404

    return response


# HTTP Error 500
def server_error(request):
    response = render_to_response('500.html',)

    response.status_code = 500

    return response
