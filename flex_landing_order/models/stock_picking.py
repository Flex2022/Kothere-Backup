from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    landing_order_id = fields.Many2one('landing.order', string='Landing Order')
    landing_orders_count = fields.Integer(compute='_compute_landing_orders_count', string='Landing Orders')

    def action_create_landing_order_using_wizerd(self):
        return {
            'name': 'Landing Order',
            'type': 'ir.actions.act_window',
            'res_model': 'landing.order',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'default_stock_picking_id': self.id,
                        'default_partner_id': self.partner_id.id,},
        }

    def get_all_landings(self):
        return {
            'name': 'Landing Order',
            'type': 'ir.actions.act_window',
            'res_model': 'landing.order',
            'view_mode': 'tree,form',
            'domain': [('stock_picking_id', '=', self.id)],
            'context': {'default_stock_picking_id': self.id},
        }

    def _compute_landing_orders_count(self):
        for order in self:
            order.landing_orders_count = self.env['landing.order'].search_count([('stock_picking_id', '=', order.id)])
