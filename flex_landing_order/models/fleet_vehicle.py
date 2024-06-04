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
    employee_id_dr = fields.Many2one('hr.employee', string='Driver Employee')

    @api.onchange('driver_id')
    def onchange_driver_id(self):
        self.employee_id_dr = self.env['hr.employee'].search([('name', '=', self.driver_id.name)], limit=1)

    # @api.depends('car_model_id')
    def _compute_loading_order_count(self):
        for car in self:
            loading_order_count = self.env['landing.order'].search([('car_model_id', '=', car.id)])
            car.loading_order_count = len(loading_order_count)