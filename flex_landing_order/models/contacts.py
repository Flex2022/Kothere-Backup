from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_driver = fields.Boolean(string='Is Driver')
    car_id = fields.Char(string='Car ID')