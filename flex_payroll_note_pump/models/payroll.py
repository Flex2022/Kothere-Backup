from odoo import api, fields, models

from datetime import date

class HrPayroll(models.Model):
    _inherit = 'hr.payslip'

    pump_driver_id = fields.Many2one('res.partner', string='Pump Driver')
    pump_workers_ids = fields.Many2many('hr.employee', string='Pump Workers')
    pump_driver_no = fields.Integer(string='Pump Driver No',compute='_compute_pump_driver_no')
    pump_workers_no = fields.Char(string='Pump Workers No',compute='_compute_pump_workers_no')

    @api.depends('pump_driver_id', 'date_from', 'date_to')
    def _compute_pump_driver_no(self):
        for record in self:
            if record.pump_driver_id:
                delivery_notes = self.env['delivery.note'].search([
                    ('driver_id', '=', record.pump_driver_id.id),
                    ('delivery_date_without_time', '>=', record.date_from),
                    ('delivery_date_without_time', '<=', record.date_to),
                    ('state', '=', 'done')
                ])
                print(delivery_notes)
                #sum pump_no of all delivery notes
                pump_no = sum(delivery_notes.mapped('pump_no'))
                record.pump_driver_no = pump_no
            else:
                record.pump_driver_no = 0

    @api.depends('pump_workers_ids', 'date_from', 'date_to')
    def _compute_pump_workers_no(self):
        for record in self:
            if record.pump_workers_ids:
                delivery_notes = self.env['delivery.note'].search([
                    ('workers_ids', 'in', record.pump_workers_ids.ids),
                    ('delivery_date_without_time', '>=', record.date_from),
                    ('delivery_date_without_time', '<=', record.date_to),
                    ('state', '=', 'done')
                ])
                #sum pump_no of all delivery notes
                pump_no = sum(delivery_notes.mapped('pump_no'))
                record.pump_workers_no = pump_no
            else:
                record.pump_workers_no = 0