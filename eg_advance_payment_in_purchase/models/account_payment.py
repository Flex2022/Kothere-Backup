from odoo import models, fields, api, _


class AccountPayment(models.Model):
    _inherit = "account.payment"

    purchase_id = fields.Many2one(comodel_name="purchase.order", string="Purchase Order")
    advance_payment = fields.Boolean(string="Advance Payment")
    advance_payment_account_id = fields.Many2one(
        'account.account',
        string="Advance Payment Account",
        default=lambda self: self._get_default_advance_payment_account(),
        help="Advance Payment Account used for customer payments configured in settings."
    )

    @api.model
    def _get_default_advance_payment_account(self):
        config_param = self.env['ir.config_parameter'].sudo()
        advance_payment_account_id = config_param.get_param('eg_advance_payment_in_purchase.advance_payment_account_id', default=None)
        return int(advance_payment_account_id) if advance_payment_account_id else False

    @api.model
    def create(self, vals):
        res = super(AccountPayment, self).create(vals)
        if 'ref' in vals:
            purchase_id = self.env["purchase.order"].search([("name", "=", vals['ref'])], limit=1)
            if purchase_id and not res.purchase_id:
                res.purchase_id = purchase_id.id
            invoice_id = self.env["account.move"].search([("name", "=", vals['ref'])], limit=1)
            if invoice_id and not res.purchase_id:
                purchase_id = self.env["purchase.order"].search([("name", "=", invoice_id.invoice_origin)], limit=1)
                if purchase_id:
                    res.purchase_id = purchase_id.id
        return res


    def action_post(self):
        res = super(AccountPayment, self).action_post()
        for rec in self:
            if rec.advance_payment and rec.advance_payment_account_id:
                rec._update_item_lines()
        return res

    def _update_item_lines(self):
        # Ensure advance payment account is used for updating
        advance_payment = self.advance_payment
        advance_payment_account = self.advance_payment_account_id

        if not advance_payment_account and not advance_payment:
            return

        for payment in self:
            for invoice in payment.move_id:
                for move_line in invoice.line_ids:
                    if move_line.account_id.account_type == 'liability_payable':
                        move_line.write({'account_id': advance_payment_account.id})