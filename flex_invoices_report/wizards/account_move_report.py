from odoo import models, fields, api, _
from odoo.exceptions import UserError
import io
import base64
import xlsxwriter
from datetime import datetime


class FlexInvoicesReport(models.TransientModel):
    _name = 'flex.account.move.report'
    _description = 'Account Move Report Wizard'

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    partner_id = fields.Many2one('res.partner', string='Customer/Vendor')
    type = fields.Selection([
        ('sale_invoices', 'Sale Invoices'),
        ('purchase_invoices', 'Purchase Invoices')],
        string="Invoice Type", default=False)
    line_ids = fields.One2many('flex.account.move.line.report', 'parent_id')

    def generate_report(self):
        # Prepare domain for fetching account move lines based on wizard criteria
        domain = [
            ('display_type', '=', 'product'),
            ('company_id', 'in', self.env.company.ids),
            ('move_id.state', '=', 'posted'),
        ]
        if self.start_date:
            domain.append(('move_id.date', '>=', self.start_date))

        if self.end_date:
            domain.append(('move_id.date', '<=', self.end_date))

        if self.partner_id:
            domain.append(('move_id.partner_id', '=', self.partner_id.id))

        if self.type:
            if self.type == 'sale_invoices':
                domain.append(('move_id.move_type', '=', 'out_invoice'))
            elif self.type == 'purchase_invoices':
                domain.append(('move_id.move_type', '=', 'in_invoice'))
        else:
            domain.append(('move_id.move_type', 'in', ('out_invoice', 'in_invoice')))

        # Fetch account move lines that match the domain
        move_lines = self.env['account.move.line'].search(domain)

        # Clear existing line_ids to avoid duplicates
        self.line_ids.unlink()

        line_ids = []
        # Create new flex.account.move.line.report records
        for line in move_lines:
            line_id = self.env['flex.account.move.line.report'].sudo().create({
                'parent_id': self.id,
                'move_line_id': line.id,
            })
            line_ids.append(line_id.id)

        self.line_ids = [(6, 0, line_ids)]

        # Return an action to open the wizard again with current values
        return {
            'name': 'Generate Account Move Report',
            'type': 'ir.actions.act_window',
            'res_model': 'flex.account.move.report',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,  # Set the res_id to the current wizard's ID
            'context': {
                'default_start_date': self.start_date,
                'default_end_date': self.end_date,
                'default_partner_id': self.partner_id.id if self.partner_id else False,

            },
        }

    @api.model
    def _get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('flex_invoices_report.flex_invoices_pdf_report_action')
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': self,
            'lines': self._lines(),
        }
        return docargs

    def generate_report_pdf(self):
        # Refresh the result
        self.generate_report()

        # Check if there are any lines to include in the report
        if not self.line_ids:
            raise UserError(_('No data to generate the report'))

        data = {}
        return self.env.ref('flex_invoices_report.flex_invoices_pdf_report_action').report_action(self, data=data)

    def generate_report_xlsx(self):
        self.generate_report()  # استدعاء التقرير قبل التصدير

        if not self.line_ids:
            raise UserError('No data to generate the report')

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet('Invoices Report')

        # تنسيقات التقرير
        title_format = workbook.add_format({'bold': True, 'align': 'center', 'font_size': 14})
        header_format = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
        data_format = workbook.add_format({'border': 1})
        date_format = workbook.add_format({'border': 1, 'num_format': 'yyyy-mm-dd'})
        number_format = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})

        # عنوان التقرير
        sheet.merge_range('A1:I1', 'Invoices Report', title_format)

        # ضبط عرض الأعمدة
        sheet.set_column('A:A', 20)  # Customer/Vendor
        sheet.set_column('B:B', 15)  # Tax Number
        sheet.set_column('C:C', 15)  # Date
        sheet.set_column('D:D', 20)  # Invoice Number
        sheet.set_column('E:E', 30)  # Description
        sheet.set_column('F:F', 20)  # Product
        sheet.set_column('G:G', 10)  # Quantity
        sheet.set_column('H:H', 15)  # Tax incl.
        sheet.set_column('I:I', 15)  # Taxes

        # فلاتر التقرير
        filters = [
            ('Date From', self.start_date.strftime('%Y-%m-%d')),
            ('Date To', self.end_date.strftime('%Y-%m-%d')),
            ('Customer/Vendor', self.partner_id.name if self.partner_id else ''),
            ('Invoice Type', dict(self._fields['type'].selection).get(self.type, '') if self.type else ''),
            ('Printing Date', datetime.today().strftime('%Y-%m-%d'))
        ]

        row = 2  # البدء من الصف الثالث
        for label, value in filters:
            sheet.write(row, 0, label, header_format)
            sheet.write(row, 1, value, date_format if isinstance(value, datetime) else data_format)
            row += 1

        # رؤوس الأعمدة
        headers = ['Customer/Vendor', 'Tax Number', 'Date', 'Invoice Number',
                   'Description', 'Product', 'Quantity', 'Tax incl.', 'Taxes']
        sheet.write_row(row, 0, headers, header_format)

        # تعبئة البيانات
        row += 1
        for line in self.line_ids:
            sheet.write(row, 0, line.partner_id.name or '', data_format)
            sheet.write(row, 1, line.tax_number or '', data_format)
            sheet.write(row, 2, line.invoice_date, date_format)
            sheet.write(row, 3, line.invoice_name or '', data_format)
            sheet.write(row, 4, line.line_description or '', data_format)
            sheet.write(row, 5, line.line_product_id.name if line.line_product_id else '', data_format)
            sheet.write(row, 6, line.line_quantity, number_format)
            sheet.write(row, 7, line.price_total, number_format)
            sheet.write(row, 8, line.tax_value, number_format)
            row += 1

        # إغلاق ملف الإكسل
        workbook.close()
        output.seek(0)

        # تشفير الملف وتخزينه كمرفق
        file_data = base64.b64encode(output.read())
        output.close()

        attachment = self.env['ir.attachment'].create({
            'name': f'Invoices_Report_{datetime.now().strftime("%Y-%m-%d")}.xlsx',
            'type': 'binary',
            'datas': file_data,
            'store_fname': f'Invoices_Report_{datetime.now().strftime("%Y-%m-%d")}.xlsx',
            'res_model': self._name,
            'res_id': self.id,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }

class FlexInvoicesLinesReport(models.TransientModel):
    _name = 'flex.account.move.line.report'
    _description = 'Account Move Report Line Wizard'

    parent_id = fields.Many2one('flex.account.move.report')
    move_line_id = fields.Many2one('account.move.line', string='move line')
    company_id = fields.Many2one('res.company', related="move_line_id.company_id")
    move_type = fields.Selection(related="move_line_id.move_id.move_type")
    currency_id = fields.Many2one('res.currency', related="move_line_id.currency_id")
    partner_id = fields.Many2one('res.partner', 'Customer/Vendor', related="move_line_id.move_id.partner_id")
    invoice_date = fields.Date('Date', related="move_line_id.move_id.invoice_date")
    tax_number = fields.Char('Tax Number',related="partner_id.vat")
    invoice_name = fields.Char('Invoice Number', related="move_line_id.move_id.name")
    line_description = fields.Char('Description', related="move_line_id.name")
    line_product_id = fields.Many2one('product.product', 'Product', related="move_line_id.product_id")
    line_quantity = fields.Float('Quantity', related="move_line_id.quantity")
    price_unit = fields.Float('Price Unit', related="move_line_id.price_unit")
    tax_ids = fields.Many2many('account.tax', 'Taxes', related="move_line_id.tax_ids")
    price_subtotal = fields.Monetary('Tax excl.', related="move_line_id.price_subtotal")
    price_total = fields.Monetary('Tax incl.', related="move_line_id.price_total")
    tax_value = fields.Monetary('Taxes Value', compute="compute_taxes_value", store=True)

    @api.depends('price_subtotal', 'price_total')
    def compute_taxes_value(self):
        for line in self:
            line.tax_value = line.price_total - line.price_subtotal
