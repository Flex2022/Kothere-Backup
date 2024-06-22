from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    advance_payment_account_id = fields.Many2one(
        'account.account',
        string="Advance Payment Account",
        help="Select the account used for advance payments",
        check_company=True,
        config_parameter='eg_advance_payment_in_purchase.advance_payment_account_id')
