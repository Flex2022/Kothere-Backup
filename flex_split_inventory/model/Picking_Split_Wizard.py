from odoo import api, fields, models


class PickingSplitWizard(models.TransientModel):
    _name = 'picking.split.wizard'
    _description = 'Picking Split Wizard'

    split_option = fields.Selection([('new', 'New'), ('existing', 'Existing')], string='Split Option')
    new_picking_id = fields.Many2one('stock.picking', string='New Picking')
    existing_picking_id = fields.Many2one('stock.picking', string='Existing Picking')