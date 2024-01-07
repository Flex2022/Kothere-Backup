from odoo import api, fields, models
from odoo.exceptions import UserError



class StockPickingWizard(models.TransientModel):
    _name = 'stock.picking.wizard'
    _description = 'Stock Picking Wizard'

    # Define your selection field here
    # For example, a simple status selection
    status_selection = fields.Selection([
        ('new_transfer', 'New Transfer'),
        ('exist_transfer', 'To Exist Transfer'),
    ], string='Select Action', default='new_transfer')

    existing_picking_id = fields.Many2one('stock.picking', string='Existing Transfer')
    def apply_action(self):
        active_ids = self.env.context.get('active_ids')
        pickings = self.env['stock.picking'].browse(active_ids)
        selected_moves = pickings.mapped('move_ids_without_package').filtered('split')

        if self.status_selection == 'new_transfer':
            # Create a new stock.picking record
            new_picking = self.env['stock.picking'].create({
                'location_id': pickings[0].location_id.id,
                'location_dest_id': pickings[0].location_dest_id.id,
                'picking_type_id': pickings[0].picking_type_id.id,
                'sourse_picking_id': pickings[0].id,
                # Add other necessary fields as per your requirements
            })
            selected_moves.write({'picking_id': new_picking.id})

        elif self.status_selection == 'exist_transfer':
            if not self.existing_picking_id:
                raise UserError('Please select an existing transfer.')
            if self.existing_picking_id.sourse_picking_id:
                raise UserError('This transfer has a source transfer.')
            self.existing_picking_id.write({'sourse_picking_id': pickings[0].id})
            selected_moves.write({'picking_id': self.existing_picking_id.id})
        for picking in pickings:
            if self.status_selection == 'new_transfer':
                picking.sourse_picking_id = new_picking.id
            elif self.status_selection == 'exist_transfer':
                picking.sourse_picking_id = self.existing_picking_id.id

        return {'type': 'ir.actions.act_window_close'}