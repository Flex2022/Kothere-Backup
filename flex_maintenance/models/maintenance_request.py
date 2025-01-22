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

    actual_hours_number = fields.Float(string='Actual Hours Number', readonly=False)
    actual_kilometres_number = fields.Float(string='Actual Kilometres Number', related='vehicle_id.odometer',
                                            readonly=False)
    odometer_unit = fields.Selection([('kilometers', 'km'), ('miles', 'mi')], 'Odometer Unit', default='kilometers',
                                     required=True, related="vehicle_id.odometer_unit", readonly=False)

    recurring_maintenance = fields.Boolean(string="Recurrent", readonly=False)


    def _compute_repair_count(self):
        for rec in self:
            rec.repair_count = self.env['repair.order'].search_count([('maintenance_request_id', '=', rec.id)])

    def create_repair_order(self):
        companies = self.company_id or self.env.company
        default_warehouse = self.env.user.with_company(companies.id)._get_default_warehouse_id()

        for rec in self:
            repair_order_vals = {
                'state': 'draft',
                'vehicle_id': rec.vehicle_id.id,
                'maintenance_request_id': rec.id,
                'picking_type_id': default_warehouse.repair_type_id.id,
                'location_dest_id': default_warehouse.repair_type_id.default_location_dest_id.id,
                'actual_hours_number': rec.actual_hours_number,
                'actual_kilometres_number': rec.actual_kilometres_number,
            }
            if repair_order_vals:
                repair = self.env['repair.order'].sudo().create(repair_order_vals)
                repair._get_picking_type()

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


