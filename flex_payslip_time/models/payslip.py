from odoo import api, fields, models

from odoo.fields import Date, Datetime

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    attendance_ids = fields.Many2many('flex.overtime', string='OverTime', compute='_compute_attendance_ids', store=True)
    total_out_work_hours = fields.Float('Total Out Work Hours', compute='_compute_total_out_work_hours',store=True)

    @api.depends('date_from', 'date_to')
    def _compute_attendance_ids(self):
        for payslip in self:
            date_from = Datetime.to_datetime(payslip.date_from) if isinstance(payslip.date_from,
                                                                              Date) else payslip.date_from
            date_to = Datetime.to_datetime(payslip.date_to) if isinstance(payslip.date_to, Date) else payslip.date_to
            payslip.attendance_ids = self.env['flex.overtime'].search([
                ('date_from', '<=', date_to),
                ('date_to', '>=', date_from),
                ('state', '=', 'approve')
            ])

    @api.depends('attendance_ids.overtime_lines')
    def _compute_total_out_work_hours(self):
        for payslip in self:
            total_hours = 0.0
            for attendance in payslip.attendance_ids:
                # Filter overtime lines for the specific employee
                employee_overtime_lines = attendance.overtime_lines.filtered(
                    lambda line: line.employee_id == payslip.employee_id)
                # Sum the 'overtime' field for the filtered lines
                total_hours += sum(line.overtime for line in employee_overtime_lines)
            payslip.total_out_work_hours = total_hours






