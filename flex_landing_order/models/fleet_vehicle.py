from odoo import api, fields, models


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    def get_all_landings(self):
        return {
            'name': 'Landing Order',
            'type': 'ir.actions.act_window',
            'res_model': 'landing.order',
            'view_mode': 'tree',
            # 'view_type': 'tree,form',
            # 'target': 'new',
            'domain': [('car_model_id', '=', self.id)],
            # 'context': {'default_car': self.id},
        }

    loading_order_count = fields.Integer(compute='_compute_loading_order_count', string='Loading Orders')

    # @api.depends('car_model_id')
    def _compute_loading_order_count(self):
        for car in self:
            loading_order_count = self.env['landing.order'].search([('car_model_id', '=', car.id)])
            car.loading_order_count = len(loading_order_count)