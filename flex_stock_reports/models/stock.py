from odoo import api, fields, models

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    receipt_permission = fields.Char(string='Warehouse Receipt Permission')
    driver_name = fields.Many2one('res.partner', string='Driver Name')
    car_number = fields.Char(string='Car Number')
    receipt_no = fields.Char(string='Receipt No')