# -*- coding: utf-8 -*-
from odoo import fields, http, SUPERUSER_ID, _
from odoo.exceptions import UserError
from odoo.http import request
import json
import functools
import base64
import logging
from datetime import datetime
_logger = logging.getLogger(__name__)
from odoo.tools import groupby
from operator import itemgetter
import werkzeug.exceptions
from odoo.tools.image import image_guess_size_from_field_name


class HttpImproved(http.Controller):

    # , website=True
    @http.route([
        '/force_report/<converter>/<reportname>.pdf',
        '/force_report/<converter>/<reportname>/<docids>.pdf',
        '/force_report/<converter>/<reportname>/<docids>/<lang>.pdf',
    ], type='http', auth='none')
    def report_routes(self, reportname, docids=None, converter=None, lang=None, **data):
        report = request.env['ir.actions.report'].sudo()
        context = dict(request.env.context)

        if lang == 'ar':
            context.update({'lang': 'ar_001'})
        if docids:
            docids = [int(i) for i in docids.split(',') if i.isdigit()]
        if data.get('options'):
            data.update(json.loads(data.pop('options')))
        if data.get('context'):
            data['context'] = json.loads(data['context'])
            context.update(data['context'])
        if converter == 'html':
            html = report.with_context(context)._render_qweb_html(reportname, docids, data=data)[0]
            return request.make_response(html)
        elif converter == 'pdf':
            pdf = report.with_context(context).sudo()._render_qweb_pdf(reportname, docids, data=data)[0]
            pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
            return request.make_response(pdf, headers=pdfhttpheaders)
        elif converter == 'text':
            text = report.with_context(context)._render_qweb_text(reportname, docids, data=data)[0]
            texthttpheaders = [('Content-Type', 'text/plain'), ('Content-Length', len(text))]
            return request.make_response(text, headers=texthttpheaders)
        else:
            raise werkzeug.exceptions.HTTPException(description='Converter %s not implemented.' % converter)

    # Force open binary fields without considering record rules (issue was from multi-company)
    @http.route([
        '/web/force/image/<string:model>/<int:id>/<string:field>',
        '/web/force/image/<string:model>/<int:id>/<string:field>/<string:filename>',
        '/web/force/image/<string:model>/<int:id>/<string:field>/<int:width>x<int:height>',
        '/web/force/image/<string:model>/<int:id>/<string:field>/<int:width>x<int:height>/<string:filename>'],
        type='http', auth="public")
    def content_image(self, xmlid=None, model='ir.attachment', id=None, field='raw',
                      filename_field='name', filename=None, mimetype=None, unique=False,
                      download=False, width=0, height=0, crop=False, access_token=None,
                      nocache=False):
        try:
            record = request.env['ir.binary'].sudo()._find_record(xmlid, model, id and int(id), access_token)
            stream = request.env['ir.binary'].sudo()._get_image_stream_from(
                record, field, filename=filename, filename_field=filename_field,
                mimetype=mimetype, width=int(width), height=int(height), crop=crop,
            )
        except UserError as exc:
            if download:
                raise request.not_found() from exc
            # Use the ratio of the requested field_name instead of "raw"
            if (int(width), int(height)) == (0, 0):
                width, height = image_guess_size_from_field_name(field)
            record = request.env.ref('web.image_placeholder').sudo()
            stream = request.env['ir.binary'].sudo()._get_image_stream_from(
                record, 'raw', width=int(width), height=int(height), crop=crop,
            )

        send_file_kwargs = {'as_attachment': download}
        if unique:
            send_file_kwargs['immutable'] = True
            send_file_kwargs['max_age'] = http.STATIC_CACHE_LONG
        if nocache:
            send_file_kwargs['max_age'] = None

        res = stream.get_response(**send_file_kwargs)
        res.headers['Content-Security-Policy'] = "default-src 'none'"
        return res

