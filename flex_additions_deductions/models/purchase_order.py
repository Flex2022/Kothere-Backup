from odoo import fields, models, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    project_invoice = fields.Many2one('project.project', string='Project Invoice')

    project_manager = fields.Many2one('res.partner', string='Project Manager')

    projects_manager = fields.Many2one('res.partner', string='Projects Manager')

    flex_deductions_ids = fields.One2many('deductions.lines', 'purchase_id', string='Deductions')

    flex_additions_ids = fields.One2many('additions.lines', 'purchase_id', string='Additions')

    there_is_access_from_company_id = fields.Boolean(string='There Is Access From Company Id',
                                                     compute='_compute_there_is_access_from_company_id')


    def _compute_there_is_access_from_company_id(self):
        for record in self:
            if record.company_id.flex_additions_deductions_ids:
                record.there_is_access_from_company_id = True
            else:
                record.there_is_access_from_company_id = False


    def _prepare_invoice(self):
        """Prepare the dict of values to create the new invoice for a purchase order.
        """
        self.ensure_one()
        move_type = self._context.get('default_move_type', 'in_invoice')

        partner_invoice = self.env['res.partner'].browse(self.partner_id.address_get(['invoice'])['invoice'])
        partner_bank_id = self.partner_id.commercial_partner_id.bank_ids.filtered_domain(['|', ('company_id', '=', False), ('company_id', '=', self.company_id.id)])[:1]

        invoice_vals = {
            'ref': self.partner_ref or '',
            'move_type': move_type,
            'narration': self.notes,
            'currency_id': self.currency_id.id,
            'partner_id': partner_invoice.id,
            'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id._get_fiscal_position(partner_invoice)).id,
            'payment_reference': self.partner_ref or '',
            'partner_bank_id': partner_bank_id.id,
            'invoice_origin': self.name,
            'invoice_payment_term_id': self.payment_term_id.id,
            'invoice_line_ids': [],
            'company_id': self.company_id.id,
            'flex_deductions_ids': [(0, 0, {
                'name': line.name,
                'deductions_id': line.deductions_id.id,
                'amount_deductions': line.amount_deductions,
                'is_percentage': line.is_percentage,
                'percentage_or_value': line.percentage_or_value,
                'tax_id': line.tax_id.id,
            }) for line in self.flex_deductions_ids],
            'flex_additions_ids': [(0, 0, {
                'name': line.name,
                'additions_id': line.additions_id.id,
                'amount_deductions': line.amount_deductions,
                'is_percentage': line.is_percentage,
                'percentage_or_value': line.percentage_or_value,
                'tax_id': line.tax_id.id,
            }) for line in self.flex_additions_ids],
        }
        return invoice_vals

