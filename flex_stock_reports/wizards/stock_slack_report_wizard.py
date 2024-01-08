from odoo import models, fields, api, _
from odoo.exceptions import UserError
from io import BytesIO
import xlsxwriter
import base64


class StockReportWizard(models.TransientModel):
    _name = 'flex.stock.slack.report.wizard'
    _description = 'Stock Slack Report Wizard'

    product_ids = fields.Many2many('product.product', string='Products')
    location_ids = fields.Many2many('stock.location', string='Locations')
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    qty_min = fields.Float(string='Min quantity')
    qty_max = fields.Float(string='Max quantity')
    stock_line_ids = fields.Many2many('stock.quant')
    excel_file = fields.Binary()
    excel_file_name = fields.Char()

    VIEW_TREE_EDITABLE = 'flex_stock_reports.view_stock_quants_tree_view'
    VIEW_PIVOT = 'stock.view_stock_quant_pivot'
    VIEW_GRAPH = 'stock.stock_quant_view_graph'

    def get_domain(self):
        domain = []

        if self.product_ids:
            domain.append(('product_id', 'in', self.product_ids.ids))

        if self.location_ids:
            domain.append(('location_id', 'in', self.location_ids.ids))

        if self.date_from:
            domain.append(('inventory_date', '>=', self.date_from))

        if self.date_to:
            domain.append(('inventory_date', '<=', self.date_to))

        if self.qty_min:
            domain.append(('quantity', '>=', self.qty_min))

        if self.qty_max:
            domain.append(('quantity', '<=', self.qty_max))

        return domain

    def get_lines(self):
        domain = self.get_domain()
        stock_line_ids = self.env['stock.quant'].search(domain)

        # Update the one2many field stock_line_ids with the new report lines
        self.stock_line_ids = stock_line_ids

    def generate_report(self):
        self.get_lines()

        # Check if there are any lines to include in the report
        if not self.stock_line_ids:
            raise UserError(_('No data to generate the report'))

        # Return the action to open the tree view for stock quant
        return {
            'name': _('Stock Slack report'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.quant',
            'view_mode': 'tree,form,pivot,graph',
            'view_id': self.env.ref(self.VIEW_TREE_EDITABLE).id,
            'views': [
                (self.env.ref(self.VIEW_TREE_EDITABLE).id, 'tree'),
                (self.env.ref(self.VIEW_PIVOT).id, 'pivot'),
                (self.env.ref(self.VIEW_GRAPH).id, 'graph'),
            ],
            'domain': [('id', 'in', self.stock_line_ids.ids)],
            'target': 'current',
        }

    def generate_report_pdf(self):
        # Refresh the result
        self.get_lines()

        # Check if there are any lines to include in the report
        if not self.stock_line_ids:
            raise UserError(_('No data to generate the report'))

        data = {}
        return self.env.ref('flex_stock_reports.report_stock_slack').report_action(self, data=data)

    @api.model
    def _get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('flex_stock_reports.report_stock_slack')
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': self,
            'lines': self._lines(),
        }
        return docargs


    def generate_report_excel(self):
        # Refresh the result
        self.get_lines()

        # Check if there are any lines to include in the report
        if not self.stock_line_ids:
            raise UserError(_('No data to generate the report'))

        # Create a workbook and add a worksheet
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # Define Excel formats
        bold = workbook.add_format({'bold': True})
        money_format = workbook.add_format({'num_format': '#,##0.00'})

        # Set the column widths for each column (adjust as needed)
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 15)

        # Write header row
        headers = ['Location', 'Product', 'On Hand Quantity', 'Reserved Quantity']
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, bold)

        # Write data rows
        for row_num, line in enumerate(self.stock_line_ids, start=1):
            worksheet.write(row_num, 0, line.location_id.name)
            worksheet.write(row_num, 1, line.product_id.name)
            worksheet.write(row_num, 2, line.quantity)
            worksheet.write(row_num, 3, line.reserved_quantity)

        # Close the workbook
        workbook.close()

        # Set Data
        self.excel_file = base64.standard_b64encode(output.getvalue())
        self.excel_file_name = "stock_slack_report.xlsx"

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/flex_stock_slack_download_xlsx_report/%s' % self.id,
            'target': 'new',
        }
