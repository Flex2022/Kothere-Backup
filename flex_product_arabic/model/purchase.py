from odoo import api, fields, models

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    product_arabic = fields.Char(string='Product AR', related='product_id.product_arabic')