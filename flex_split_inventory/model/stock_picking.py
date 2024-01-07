from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError


class stock_picking(models.Model):
    _inherit = 'stock.picking'
    _description = 'stock_picking'

    # related_picking_id = fields.Many2one('stock.picking', string='Related Picking')
    sourse_picking_id = fields.Many2one('stock.picking', string='Sourse Picking' , domain="[('id', '!=', id)]")
    count_picking = fields.Integer(string='Related Pickings', compute='compute_count_picking')

    def select_all_moves(self):
        for move in self.move_ids_without_package:
            move.split = True

    def deselect_all_moves(self):
        for move in self.move_ids_without_package:
            move.split = False

    def action_stock_picking_wizard(self):
        # This method opens the wizard
        return {
            'name': 'Stock Picking Wizard',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('flex_split_inventory.view_stock_picking_wizard_form').id,
            'target': 'new',
            'context': {
                'default_status_selection': 'new_transfer',  # Set default values if needed
                'active_ids': self.ids,  # Pass the current stock picking's ID
                'default_picking_type_id': self.picking_type_id.id,
                # 'default_sourse_picking_id': self.id,
            }
        }

    # def action_view_related_pickings(self):
    #     self.ensure_one()
    #     action = self.env.ref('stock.action_picking_tree_all').read()[0]
    #     action['domain'] = [('sourse_picking_id', '=', self.id)]
    #     action['context'] = {'default_sourse_picking_id': self.id}
    #     return action

    def action_view_related_pickings(self):
        account_move = self.env['stock.picking'].search([('sourse_picking_id', '=', self.id)])
        return {
            'name': 'Stock Pickings',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', account_move.ids)],
            # 'context': {'default_sourse_picking_id': self.id},
        }


    def compute_count_picking(self):
        picking_order = self.env['stock.picking'].search([('sourse_picking_id', '=', self.id)])
        self.count_picking = len(picking_order)
