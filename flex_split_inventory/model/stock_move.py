from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'
    _description = 'stock_move'

    split = fields.Boolean(string='Split', default=False)