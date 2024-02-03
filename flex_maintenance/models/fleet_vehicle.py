from odoo import api, fields, models, _


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    hours_number = fields.Integer(string='Hours Number')
    kilometres_number = fields.Integer(string='Kilometres Number')
    maintenance_count = fields.Integer(string='Maintenance Count', compute='_compute_maintenance_count')
    repair_count = fields.Integer(string='Repair Count', compute='_compute_repair_count')

    def _compute_maintenance_count(self):
        for rec in self:
            rec.maintenance_count = self.env['maintenance.request'].search_count([('vehicle_id', '=', rec.id)])

    def _compute_repair_count(self):
        for rec in self:
            rec.repair_count = self.env['repair.order'].search_count([('vehicle_id', '=', rec.id)])

    def get_maintenance_request(self):
        return {
            'name': _('Maintenance Request'),
            'domain': [('vehicle_id', '=', self.id)],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'maintenance.request',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'target': 'current',
        }

    def get_repair_order(self):
        return {
            'name': _('Repair'),
            'domain': [('vehicle_id', '=', self.id)],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'repair.order',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'target': 'current',
        }

