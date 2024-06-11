from odoo import models, fields, api, _


class StockMoveReportWizard(models.TransientModel):
    _name = 'stock.move.report.wizard'
    _description = 'Stock Move Report Wizard'

    vehicle_ids = fields.Many2many('fleet.vehicle', string='Vehicles')
    line_ids = fields.Many2many('stock.move', string='Stock Moves')

    # def generate_report(self):
    #     # Call the report action
    #     action = self.env.ref('your_module_name.action_stock_move_report').read()[0]
    #     action['context'] = dict(self.env.context, active_id=self.id)
    #     return action

    @api.onchange('vehicle_ids')
    def generate_lines(self):
        if self.vehicle_ids:
            stock_moves = self.env['stock.move'].search([('vehicle_id', 'in', self.vehicle_ids.ids)])
            self.line_ids = [(6, 0, stock_moves.ids)]

        # Return to this wizard
        return {
            'name': _('Vehicle Stock Move Report'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move.report.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new'}

    # stock_valuation_layer_ids
