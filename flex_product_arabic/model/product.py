from odoo import api, fields, models

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_arabic = fields.Char(string='Product AR')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    product_arabic = fields.Char(string='Product AR',related='product_tmpl_id.product_arabic')