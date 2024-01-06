from odoo import models, fields, api, _
from io import BytesIO
from odoo.tools.misc import xlsxwriter
import base64
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


class PurchaseReportWizard(models.TransientModel):
    _name = 'purchase.cost.report.wizard'
    _description = 'Purchase Report Wizard'

    product_ids = fields.Many2many('product.product', string='Products')
    vendor_ids = fields.Many2many('res.partner', string='Vendors')
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    purchase_line_ids = fields.Many2many('purchase.order.line')
    excel_file = fields.Binary()
    excel_file_name = fields.Char()

    def get_domain(self):
        domain = []

        if self.product_ids:
            domain += [('product_id', 'in', self.product_ids.ids)]

        if self.vendor_ids:
            domain += [('partner_id', 'in', self.vendor_ids.ids)]

        if self.date_from:
            domain += [('order_id.date_approve', '>=', self.date_from)]

        if self.date_to:
            domain += [('order_id.date_approve', '<=', self.date_to)]
        return domain

    def get_lines(self):
        domain = self.get_domain()
        purchase_line_ids = self.env['purchase.order.line'].search(domain)

        # Delete existing report lines
        self.purchase_line_ids = [(5, 0, [])]
        # Update the one2many field line_ids with the new report lines
        self.purchase_line_ids = purchase_line_ids

    def generate_report(self):
        self.get_lines()
        purchase_lines = self.purchase_line_ids

        # Check if there are any lines to include in the report
        if not self.purchase_line_ids:
            raise UserError(_('No data to generate the report'))

        # Return the action to open the tree view for purchase.order.line
        return {
            'name': _('Purchase costs report'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order.line',
            'view_mode': 'tree,form',
            'view_id': self.env.ref('flex_purchase_reports.view_purchase_lines_tree_view').id,
            'views': [(self.env.ref('flex_purchase_reports.view_purchase_lines_tree_view').id, 'tree'),
                      (self.env.ref('flex_purchase_reports.view_purchase_lines_pivot_view').id, 'pivot')],
            'domain': [('id', 'in', purchase_lines.ids)],
            'target': 'current',
            'context': {
                'default_filter_product_id': self.product_ids.ids,
                'default_filter_partner_id': self.vendor_ids.ids,
                'default_filter_date_from': self.date_from,
                'default_filter_date_to': self.date_to,
            },
        }

    def generate_report_pdf(self):
        # Refresh the result
        self.get_lines()

        # Check if there are any lines to include in the report
        if not self.purchase_line_ids:
            raise UserError(_('No data to generate the report'))

        data = {}
        return self.env.ref('flex_purchase_reports.report_purchase_costs').report_action(self, data=data)

    @api.model
    def _get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('flex_purchase_reports.report_purchase_costs')
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': self,
            'lines': self._lines(),
        }
        return docargs

    def generate_report_excel(self):
        # Get domain
        domain = self.get_domain()

        # Your existing code to filter purchase lines
        purchase_lines = self.env['purchase.order.line'].search(domain)

        # Check if there are any lines to include in the report
        if not purchase_lines:
            raise UserError(_('No data to generate the report'))

        # Create a workbook and add a worksheet
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # Define Excel formats
        bold = workbook.add_format({'bold': True})
        money_format = workbook.add_format({'num_format': '#,##0.00'})

        ## Set the column widths for each column
        worksheet.set_column('A:A', 15)  # Adjust width for column A
        worksheet.set_column('B:B', 35)  # Adjust width for column B
        worksheet.set_column('C:C', 30)  # Adjust width for column C
        worksheet.set_column('D:D', 25)  # Adjust width for column D
        worksheet.set_column('E:E', 10)  # Adjust width for column E
        worksheet.set_column('F:F', 15)  # Adjust width for column F
        worksheet.set_column('G:G', 15)
        worksheet.set_column('H:H', 10)

        # Write header row
        headers = ['Order Reference', 'Product', 'Vendor', 'Confirmation Date ', 'Quantity', 'Unit', 'Price',
                   'Subtotal', 'Currency']
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, bold)

        # Write data rows
        for row_num, line in enumerate(purchase_lines, start=1):
            worksheet.write(row_num, 0, line.order_id.name)
            worksheet.write(row_num, 1, line.product_id.name)
            worksheet.write(row_num, 2, line.partner_id.name)
            # Format the confirmation date
            confirmation_date = fields.Datetime.to_string(line.date_approve) if line.date_approve else ''
            worksheet.write(row_num, 3, confirmation_date)
            worksheet.write(row_num, 4, line.product_qty)
            worksheet.write(row_num, 5, line.product_uom.name)
            worksheet.write(row_num, 6, line.price_unit, money_format)
            worksheet.write(row_num, 7, line.price_subtotal, money_format)
            worksheet.write(row_num, 8, line.currency_id.name if line.currency_id else '')

        # Close the workbook
        workbook.close()

        # Set Data
        self.excel_file = base64.standard_b64encode(output.getvalue())
        self.excel_file_name = "purchase_costs_report.xlsx"

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/flex_download_xlsx_report/%s' % self.id,
            'target': 'new',
        }
