# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    date_stock = fields.Datetime(string='Stock Date', groups="hz_stock_date.group_stock_date",
                                 help='If set, It will be the real date in inventory moves.')
