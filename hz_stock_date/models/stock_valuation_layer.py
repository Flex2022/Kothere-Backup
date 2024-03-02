# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class StockValuationLayer(models.Model):
	_inherit = 'stock.valuation.layer'

	@api.model_create_multi
	def create(self, vals_list):
		""" update create_date for valuations that are linked to quant/picking with date_stock """
		stock_valuations = super(StockValuationLayer, self).create(vals_list)
		for valuation in stock_valuations.filtered(lambda v: v.stock_move_id.quant_id.date_stock):
			valuation._write({'create_date': valuation.stock_move_id.quant_id.date_stock})
		for valuation in stock_valuations.filtered(lambda v: v.stock_move_id.picking_id.date_stock):
			valuation._write({'create_date': valuation.stock_move_id.picking_id.date_stock})
		return stock_valuations

