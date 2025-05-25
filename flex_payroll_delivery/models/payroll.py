from odoo import api, fields, models

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    distance_per_km_order = fields.Float(string='Distance per KM', default=0.0,compute='_compute_distance_per_km')


    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_distance_per_km(self):
        for record in self:
            if record.employee_id:
                delivery_orders = self.env['stock.picking'].search([
                    ('employee_id.id', '=', record.employee_id.id),
                    ('date_done', '>=', record.date_from),
                    ('date_done', '<=', record.date_to),
                    ('picking_type_code', '=', 'outgoing'),
                    ('state', '=', 'done')
                ])
                print(delivery_orders)
                # Sum the distance_per_km of all delivery orders
                distance_per_km = sum(delivery_orders.mapped('distance_per_km'))
                record.distance_per_km_order = distance_per_km
            else:
                record.distance_per_km_order = 0.0