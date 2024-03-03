# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    date_stock = fields.Datetime(string='Stock Date', groups="hz_stock_date.group_stock_date",
                                 help='If set, It will be the real date in inventory moves.')

    @api.model
    def _get_inventory_fields_write(self):
        """ Returns a list of fields user can edit when he want to edit a quant in `inventory_mode`. """
        return super(StockQuant, self)._get_inventory_fields_write() + ['date_stock']

    def _get_inventory_move_values(self, qty, location_id, location_dest_id, package_id=False, package_dest_id=False):
        res = super()._get_inventory_move_values(qty, location_id, location_dest_id, package_id, package_dest_id)
        res.update({'quant_id': self.id})
        return res

    def _apply_inventory(self):
        res = super(StockQuant, self)._apply_inventory()
        self.write({'date_stock': False})
        return res
