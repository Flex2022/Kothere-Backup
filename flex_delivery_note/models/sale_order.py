from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    delivery_note_ids = fields.One2many('delivery.note', 'picking_id', string='Delivery Notes', compute='_compute_delivery_notes')
    delivery_note_count = fields.Integer(string="Delivery Notes", compute='_compute_delivery_notes')

    @api.depends('picking_ids')
    def _compute_delivery_notes(self):
        for rec in self:
            delivery_note_ids = self.env['delivery.note'].search([('picking_id', 'in', self.picking_ids.ids)])
            rec.delivery_note_ids = delivery_note_ids.ids
            rec.delivery_note_count = len(delivery_note_ids)

    def action_view_delivery_notes(self):
        return {
            'name': 'Delivery Notes',
            'type': 'ir.actions.act_window',
            'res_model': 'delivery.note',
            'view_mode': 'tree,form',
            'domain': [('picking_id', 'in', self.picking_ids.ids)],
            # 'context': {
            #     'default_picking_id': self.id
            # },
        }

