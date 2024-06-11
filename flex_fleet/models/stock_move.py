from odoo import models, fields


class StockMove(models.Model):
    _inherit = 'stock.move'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
