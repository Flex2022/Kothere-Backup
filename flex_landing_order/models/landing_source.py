from odoo import api, fields, models

class LandingSource(models.Model):
    _name = "landing.source"
    _description = "Landing Source"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(
        string='Name',
        required=True,
        tracking=True,
    )
    desition = fields.Char(
        string='Desition',
        tracking=True,
    )
    source = fields.Char(
        string='Source',
        tracking=True,
    )
    amount = fields.Float(
        string='Amount',
        tracking=True,
    )