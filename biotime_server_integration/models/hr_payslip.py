from odoo import api, fields, models
from datetime import datetime, time


class Payslip(models.Model):
    _inherit = 'hr.payslip'

    attendance_hours_deduction = fields.Float(
        string='Attendance Hours Deduction',
        compute='_compute_attendance_hours_deduction',
        store=True
    )

    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_attendance_hours_deduction(self):
        for payslip in self:
            if payslip.date_from and payslip.date_to:
                start_time = datetime.combine(payslip.date_from, time.min)
                end_time = datetime.combine(payslip.date_to, time.max)
                domain = [
                    ('employee_id', '=', payslip.employee_id.id),
                    ('check_in', '>=',start_time),
                    ('check_in', '<=', end_time),
                    ('state', '=', 'confirm')
                ]
                attendances = self.env['hr.attendance'].search(domain)
                payslip.attendance_hours_deduction = sum(attendances.mapped('hours_deduction'))
            else:
                payslip.attendance_hours_deduction = 0
