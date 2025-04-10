from odoo import api, fields, models

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    product_arabic = fields.Char(string='Product AR', related='product_id.product_arabic')



class MaterialPurchaseRequisitionLine(models.Model):
    _inherit = 'material.purchase.requisition.line'

    product_arabic = fields.Char(string='Product AR', related='product_id.product_arabic')