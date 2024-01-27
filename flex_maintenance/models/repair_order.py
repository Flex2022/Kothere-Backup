from odoo import api, fields, models, _
from odoo.exceptions import UserError


class RepairOrder(models.Model):
    _inherit = 'repair.order'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    driver_id = fields.Many2one('res.partner', string='Driver', related='vehicle_id.driver_id')
    license_plate = fields.Char(string='License Plate', related='vehicle_id.license_plate')
    maintenance_request_id = fields.Many2one('maintenance.request', string='Maintenance Request')
    # vendor_id = fields.Many2one('res.partner', string='Vendor')
    # purchase_count = fields.Integer(string='Purchase Count', compute='_compute_purchase_count')

    # def _compute_purchase_count(self):
    #     for rec in self:
    #         rec.purchase_count = self.env['purchase.order'].search_count([('repair_order_id', '=', rec.id)])

    # def create_purchase_order(self):
    #     order_line = []
    #     if not self.vendor_id:
    #         raise UserError(_('Please Select Vendor'))
    #     for line in self.move_ids:
    #         order_line.append((0, 0, {
    #             'product_id': line.product_id.id,
    #             'product_qty': line.product_uom_qty,
    #         }))
    #     order = self.env['purchase.order'].create({
    #         'partner_id': self.vendor_id.id,
    #         'repair_order_id': self.id,
    #         'order_line': order_line,
    #     })
    #
    # def get_purchase_order(self):
    #     return {
    #         'name': _('Purchase Order'),
    #         'domain': [('repair_order_id', '=', self.id)],
    #         'view_type': 'form',
    #         'view_mode': 'tree,form',
    #         'res_model': 'purchase.order',
    #         'type': 'ir.actions.act_window',
    #         'view_id': False,
    #         'target': 'current',
    #     }

#
# class PurchaseOrder(models.Model):
#     _inherit = 'purchase.order'
#
#     repair_order_id = fields.Many2one('repair.order', string='Repair Order')