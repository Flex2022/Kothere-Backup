from odoo import api, fields, models, _
from odoo.exceptions import UserError


class RepairOrder(models.Model):
    _inherit = 'repair.order'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    driver_id = fields.Many2one('res.partner', string='Driver', related='vehicle_id.driver_id')
    license_plate = fields.Char(string='License Plate', related='vehicle_id.license_plate')
    maintenance_request_id = fields.Many2one('maintenance.request', string='Maintenance Request')
    purchase_count = fields.Integer(string='Purchase Count', compute='_compute_purchase_count')

    @api.depends('move_ids')
    def _compute_purchase_count(self):
        for rec in self:
            rec.purchase_count = len(rec.move_ids.created_purchase_line_ids.order_id)
            purchase_order_ids = (self.move_ids.created_purchase_line_ids.order_id).ids
            print(purchase_order_ids, 'purchase_order_ids')

    def get_purchase_order(self):
        purchase_order_ids = (self.move_ids.created_purchase_line_ids.order_id).ids

        return {
            'name': _('Purchase Order'),
            'domain': [('id', 'in', purchase_order_ids)],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'target': 'current',
        }

