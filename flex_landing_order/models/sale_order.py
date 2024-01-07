from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    landing_order_id = fields.Many2one('landing.order', string='Landing Order')
    order_type = fields.Selection([
        ('landing', 'Landing Order'),
        ('sale', 'Sale Order')],
        string='Order Type',
        default=False)
    landing_orders_count = fields.Integer(compute='_compute_landing_orders_count', string='Landing Orders')

    def action_create_landing_order_using_wizerd(self):
        return {
            'name': 'Landing Order',
            'type': 'ir.actions.act_window',
            'res_model': 'landing.order',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'default_order_id': self.id},
        }

    def get_all_landings(self):
        return {
            'name': 'Landing Order',
            'type': 'ir.actions.act_window',
            'res_model': 'landing.order',
            'view_mode': 'tree',
            'view_type': 'tree',
            # 'target': 'new',
            'domain': [('order_id', '=', self.id)],
            'context': {'default_order_id': self.id},
        }

    def _compute_landing_orders_count(self):
        for order in self:
            order.landing_orders_count = self.env['landing.order'].search_count([('order_id', '=', order.id)])

    @api.onchange('order_type')
    def _onchange_order_type(self):
        if self.landing_orders_count > 0:
            raise UserError(
                _('You can not change the order type to landing order because there is landing orders related to this sale order'))