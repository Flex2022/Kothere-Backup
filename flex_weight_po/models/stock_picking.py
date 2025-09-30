from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    purchase_weight_id = fields.Many2one('flex.purchase.weight', string="Purchase Weight")
    truck_number = fields.Char(string='Truck No', related='purchase_weight_id.truck_number')
    driver_name = fields.Char(string="Driver Name", related='purchase_weight_id.driver_name')
    receipt_number = fields.Char(string="Receipt Number", related='purchase_weight_id.receipt_number')

