import mimetypes
import json
import logging
from eho.server.utils import xml

from flask import abort, request, Blueprint, Response
from werkzeug.datastructures import MIMEAccept


class Rest(Blueprint):
    def route(self, rule, **options):
        def decorator(func):
            endpoint = options.pop('endpoint', func.__name__)

            def handler(**kwargs):
                # extract response content type
                resp_type = request.accept_mimetypes
                type_suffix = kwargs.pop('resp_type', None)
                if type_suffix:
                    suffix_mime = mimetypes.guess_type("res." + type_suffix)[0]
                    if suffix_mime:
                        resp_type = MIMEAccept([(suffix_mime, 1)])
                request.resp_type = resp_type

                # extract fields (column selection)
                fields = list(set(request.args.getlist('fields')))
                fields.sort()
                request.fields_selector = fields

                return func(**kwargs)

            self.add_url_rule(rule, endpoint, handler, **options)
            ext_rule = rule + '.<resp_type>'
            self.add_url_rule(ext_rule, endpoint, handler, **options)

            return func

        return decorator


resp_type_json = MIMEAccept([("application/json", 1)])
resp_type_xml = MIMEAccept([("application/xml", 1)])


def render(res=None, resp_type=None, status=200, **kwargs):
    if not res:
        res = {}
    if type(res) is dict:
        res.update(kwargs)
    elif kwargs:
        # can't merge kwargs into the non-dict res
        abort_and_log(500, "Non-dict and non-empty kwargs passed to render")

    status = getattr(request, 'resp_status', status)

    if not resp_type:
        resp_type = getattr(request, 'resp_type', resp_type_json)

    body = None
    if "application/json" in resp_type:
        resp_type = resp_type_json
        body = json.dumps(res)
    elif "application/xml" in resp_type:
        resp_type = resp_type_xml
        body = xml.dumps(res)
    else:
        raise abort_and_log(400, "%s isn't supported" % resp_type)

    return Response(response=body, status=status, mimetype=resp_type.__str__())


def request_data():
    # should check body, content type, etc
    # should support different request types
    return json.loads(request.data)


def abort_and_log(code, descr):
    logging.error("Request aborted with code %s and msg '%s'" % (code, descr))
    abort(code, description=descr)