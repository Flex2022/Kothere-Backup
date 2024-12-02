from odoo import api, fields, models

class StockMove(models.Model):
    _inherit = 'stock.move'

    trilla_load_per_pill = fields.Char('Trilla load per pill')