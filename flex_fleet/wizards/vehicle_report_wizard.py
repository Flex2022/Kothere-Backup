from odoo import models, fields, api, _


class StockMoveReportWizard(models.TransientModel):
    _name = 'stock.move.report.wizard'
    _description = 'Stock Move Report Wizard'

    vehicle_ids = fields.Many2many('fleet.vehicle', string='Vehicles')
    line_ids = fields.Many2many('stock.move', string='Stock Moves', compute='_compute_generate_lines', store=True)
    all_vehicles = fields.Boolean('All vehicles')

    def action_print_pdf_report(self):
        data = {}
        return self.env.ref('flex_fleet.stock_move_report_wizard_print').report_action(self, data=data)

    @api.model
    def _get_report_values(self, docids, data=None):
        report_obj = self.env['stock.move.report.wizard']
        report = report_obj._get_report_from_name('flex_fleet.stock_move_report_wizard_print')
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': self,
            'lines': self._lines(),
        }
        return docargs

    @api.depends('vehicle_ids', 'all_vehicles')
    def _compute_generate_lines(self):
        for wizard in self:
            if wizard.vehicle_ids or wizard.all_vehicles:
                domain = [('vehicle_id', '!=', False)] if wizard.all_vehicles else [
                    ('vehicle_id', 'in', wizard.vehicle_ids.ids)]
                domain += [('company_id', 'in', self.env.user.company_id.ids)]
                stock_moves = self.env['stock.move'].search(domain)
                wizard.line_ids = [(6, 0, stock_moves.ids)]
            else:
                wizard.line_ids = [(6, 0, [])]

    # No need to return an action from a compute method, it just sets the computed fields
