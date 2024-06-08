from odoo import models, fields


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    license_count = fields.Integer(string='Driving Licenses', compute='_compute_license_count')
    vehicle_insurance_count = fields.Integer(string='Vehicle Insurances', compute='_compute_vehicle_insurance_count')

    def _compute_license_count(self):
        for vehicle in self:
            vehicle.license_count = self.env['flex.approval.renew_driving_license'].search_count([
                ('vehicle_id', '=', vehicle.id)
            ])

    def _compute_vehicle_insurance_count(self):
        for vehicle in self:
            vehicle.vehicle_insurance_count = self.env['flex.approval.renew_vehicle_insurance'].search_count([
                ('vehicle_id', '=', vehicle.id)
            ])

    def action_view_licenses(self):
        self.ensure_one()
        return {
            'name': 'Vehicle Driving Licenses',
            'domain': [('vehicle_id', '=', self.id)],
            'res_model': 'flex.approval.renew_driving_license',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'context': {'default_vehicle_id': self.id}
        }

    def action_view_insurances(self):
        self.ensure_one()
        return {
            'name': 'Vehicle Insurances',
            'domain': [('vehicle_id', '=', self.id)],
            'res_model': 'flex.approval.renew_vehicle_insurance',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'context': {'default_vehicle_id': self.id}
        }
