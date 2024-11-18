# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta


class OmegaFilters(models.TransientModel):
    _name = 'get.munch.pol'
    _description = 'Get PO lines'

    order_no = fields.Char(string='PO Number', required=True)
    product_by = fields.Selection(
        [('default_code', 'Internal Reference'), ('barcode', 'Barcode')],
        string='Add Product By',
        required=True,
        default='default_code'
    )
    purchase_id = fields.Many2one('purchase.order', string='Purchase Order')

    def action_confirm(self):
        if not self.purchase_id:
            raise ValidationError(_('This wizard should be opened from purchase order screen'))
        return self.purchase_id._load_munch_pol(order_no=self.order_no)
