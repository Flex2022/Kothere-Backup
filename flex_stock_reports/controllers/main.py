# -*- coding: utf-8 -*-
import base64
from odoo import http
from odoo.http import content_disposition, request


class VATReportXLSXDownload(http.Controller):

    @http.route(
        ["/web/binary/flex_stock_slack_download_xlsx_report/<int:file>"],
        type='http',
        auth="public",
        website=True,
        sitemap=False)
    def download_report_stock_slack_excel(self, file=None, **post):
        if file:
            file_id = request.env['flex.stock.slack.report.wizard'].browse([file])
            return self.download_document(model='flex.stock.slack.report.wizard', id=file_id.id, field='excel_file',
                                          filename=file_id.excel_file_name)
        return False

    def download_document(self, model, field, id, filename=None, **kw):
        """ Download link for files stored as binary fields.
        :param str model: name of the model to fetch the binary from
        :param str field: binary field
        :param str id: id of the record from which to fetch the binary
        :param str filename: field holding the file's name, if any
        :returns: :class:`werkzeug.wrappers.Response`
        """
        # Model = request.registry[model]
        # cr, uid, context = request.cr, request.uid, request.context
        fields = [field]
        uid = request.session.uid
        model_obj = request.env[model].with_user(uid)
        res = model_obj.browse(int(id)).read(fields)[0]
        filecontent = base64.b64decode(res.get(field) or '')
        if not filecontent:
            return request.not_found()
        else:
            if not filename:
                filename = '%s_%s.xlsx' % (model.replace('.', '_'), id)
        return request.make_response(filecontent,
                                     [('Content-Type', 'application/vnd.ms-excel'),
                                      ('Content-Disposition', content_disposition(filename))])
