from odoo import models, fields, api, _
from odoo.exceptions import UserError


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


class FlexInvoicesLinesReport(models.TransientModel):
    _name = 'flex.account.move.line.report'
    _description = 'Account Move Report Line Wizard'

    parent_id = fields.Many2one('flex.account.move.report')
    move_line_id = fields.Many2one('account.move.line', string='move line')
    company_id = fields.Many2one(related="move_line_id.company_id")
    move_type = fields.Selection(related="move_line_id.move_id.move_type")
    currency_id = fields.Many2one(related="move_line_id.currency_id")
    partner_id = fields.Many2one('res.partner', 'Customer/Vendor', related="move_line_id.move_id.partner_id")
    invoice_date = fields.Date('Date', related="move_line_id.move_id.invoice_date")
    invoice_name = fields.Char('Invoice Number', related="move_line_id.move_id.name")
    line_description = fields.Char('Description', related="move_line_id.name")
    line_product_id = fields.Many2one('product.product', 'Product', related="move_line_id.product_id")
    line_quantity = fields.Float('Quantity', related="move_line_id.quantity")
    price_unit = fields.Float('Value', related="move_line_id.price_unit")
    tax_ids = fields.Many2many('account.tax', 'Taxes', related="move_line_id.tax_ids")
    price_subtotal = fields.Monetary('Tax excl.', related="move_line_id.price_subtotal")
