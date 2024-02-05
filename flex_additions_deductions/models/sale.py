from odoo import api, fields, models, Command


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    project_invoice = fields.Many2one('project.project', string='Project Invoice')

    deductions_no = fields.Integer('Deductions No', default=0)

    def set_line_number(self):
        # every time click on set line number deductions_no will be incremented by 1
        for record in self:
            record.deductions_no += 1
            record.write({'deductions_no': record.deductions_no})

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        self.set_line_number()
        return res

    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()

        values = {
            'ref': self.client_order_ref or '',
            'move_type': 'out_invoice',
            'narration': self.note,
            'currency_id': self.currency_id.id,
            'campaign_id': self.campaign_id.id,
            'medium_id': self.medium_id.id,
            'source_id': self.source_id.id,
            'team_id': self.team_id.id,
            'partner_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id._get_fiscal_position(self.partner_invoice_id)).id,
            'invoice_origin': self.name,
            'invoice_payment_term_id': self.payment_term_id.id,
            'invoice_user_id': self.user_id.id,
            'payment_reference': self.reference,
            'transaction_ids': [Command.set(self.transaction_ids.ids)],
            'company_id': self.company_id.id,
            'invoice_line_ids': [],
            'user_id': self.user_id.id,
            'project_invoice_from_sale_order': self.project_invoice.id,
        }
        if self.journal_id:
            values['journal_id'] = self.journal_id.id
        return values

    # def _prepere_invoice(self):
    #     res = super(SaleOrder, self)._prepere_invoice()
    #     res.update({'deductions_no': self.deductions_no})
    #     return res

    # def write(self, vals):
    #     res = super(SaleOrder, self).write(vals)
    #     self.set_line_number()
    #     return res
