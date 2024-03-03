# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class StockMove(models.Model):
	_inherit = 'stock.move'

	quant_id = fields.Many2one('stock.quant', string='Quant')

	def _action_done(self, cancel_backorder=False):
		""" passing stock_date to stock.move and it's stock.move.line """
		result = super(StockMove, self)._action_done(cancel_backorder=cancel_backorder)
		for move in result.filtered(lambda sm: sm.quant_id.date_stock):
			move.write({'date': move.quant_id.date_stock})
			if move.move_line_ids:
				move.move_line_ids.write({'date': move.quant_id.date_stock})
		for move in result.filtered(lambda sm: sm.picking_id.date_stock):
			move.write({'date': move.picking_id.date_stock})
			if move.move_line_ids:
				move.move_line_ids.write({'date': move.picking_id.date_stock})
		return result

	def _prepare_account_move_vals(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost):
		""" passing stock_date to accounting entry """
		move_vals = super(StockMove, self)._prepare_account_move_vals(credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost)
		if self.quant_id.date_stock:
			move_vals.update({'date': self.quant_id.date_stock.date()})
		elif self.picking_id.date_stock:
			move_vals.update({'date': self.picking_id.date_stock.date()})
		return move_vals

