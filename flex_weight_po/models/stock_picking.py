from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    purchase_weight_id = fields.Many2one('flex.purchase.weight', string="Purchase Weight")