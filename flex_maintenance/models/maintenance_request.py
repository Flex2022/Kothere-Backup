from odoo import api, fields, models, _


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    maintenance_for = fields.Selection(selection_add=[('vehicle', 'Vehicle')], ondelete={'vehicle': 'cascade'})
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    driver_id = fields.Many2one('res.partner', string='Driver', related='vehicle_id.driver_id')
    license_plate = fields.Char(string='License Plate', related='vehicle_id.license_plate')
    hours_number = fields.Integer(string='Hours Number', related='vehicle_id.hours_number')
    kilometres_number = fields.Integer(string='Kilometres Number', related='vehicle_id.kilometres_number')
    repair_count = fields.Integer(string='Repair Count', compute='_compute_repair_count')

    def _compute_repair_count(self):
        for rec in self:
            rec.repair_count = self.env['repair.order'].search_count([('maintenance_request_id', '=', rec.id)])

    def create_repair_order(self):
        for rec in self:
            repair_order_vals = {
                'vehicle_id': rec.vehicle_id.id,
                'maintenance_request_id': rec.id,
                'driver_id': rec.driver_id.id,
                'scheduled_date': fields.Datetime.now(),
                'user_id': self.env.user.id,  # Use self.env.user.id to get the user's ID
                'company_id': rec.company_id.id,  # Use rec.company_id.id to get the company's ID
            }

            # Create repair order using create method
            self.env['repair.order'].create(repair_order_vals)

    def get_repair_order(self):
        return {
            'name': _('Repair'),
            'domain': [('maintenance_request_id', '=', self.id)],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'repair.order',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'target': 'current',
        }
