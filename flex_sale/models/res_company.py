from odoo import fields, models, api


class ResCompany(models.Model):
    _name = 'res.company'
    _inherit = 'res.company'

    bank_account_id = fields.Many2one(
        'res.partner.bank', 'Bank Account Number',
        tracking=True,
        help='Company bank account.')
