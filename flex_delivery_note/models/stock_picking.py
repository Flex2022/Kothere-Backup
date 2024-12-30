from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    delivery_note_ids = fields.One2many('delivery.note', 'picking_id', string='Delivery Notes')
    delivery_note_count = fields.Integer(string="Delivery Notes", compute='_compute_delivery_note_count')

    @api.depends('delivery_note_ids')
    def _compute_delivery_note_count(self):
        for rec in self:
            rec.delivery_note_count = len(rec.delivery_note_ids)

    def action_new_delivery_note(self):
        return {
            'name': 'Delivery Note',
            'type': 'ir.actions.act_window',
            'res_model': 'delivery.note',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {
                'default_picking_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_product_ids': self.move_ids_without_package.product_id.ids,
                # 'default_quantity': sum(self.move_ids_without_package.mapped('quantity')),
            },
        }

    def action_view_delivery_notes(self):
        return {
            'name': 'Delivery Notes',
            'type': 'ir.actions.act_window',
            'res_model': 'delivery.note',
            'view_mode': 'tree,form',
            'domain': [('picking_id', 'in', self.ids)],
            'context': {
                'default_picking_id': self.id
            },
        }

