from datetime import datetime, time
from odoo import models, fields, api

class FlexOverTime(models.Model):
    _name = 'flex.overtime'
    _description = 'Flex Overtime'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    state = fields.Selection([('draft', 'Draft'),('submit','Submit'),('approve_line_manager', 'Approve Line Manager'),('approve','Approved')], string='State', default='draft', tracking=True, copy=False)
    name = fields.Char(string='Name', compute='_compute_name', readonly=False, store=True)
    date_from = fields.Datetime(string='Date From', required=True)
    date_to = fields.Datetime(string='Date To', required=True)
    overtime_lines = fields.One2many('flex.overtime.line', 'flex_overtime_id', string='Overtime Lines', compute='_compute_overtime_lines',store=True,readonly=False)

    @api.depends('date_from', 'date_to')
    def _compute_name(self):
        for record in self:
            if record.date_from and record.date_to:
                record.name = f"{record.date_from.strftime('%Y-%m-%d %H:%M:%S')} - {record.date_to.strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                record.name = ''

    @api.depends('date_from', 'date_to')
    def _compute_overtime_lines(self):
        for flex in self:
            flex.overtime_lines = [(5, 0, 0)]  # Clear existing lines
            if flex.date_from and flex.date_to:
                start_datetime = flex.date_from
                end_datetime = flex.date_to

                # Find attendances within the period
                attendances = self.env['hr.attendance'].search([
                    ('check_in', '<=', end_datetime),
                    ('check_out', '>=', start_datetime)
                ])

                lines = []
                for attendance in attendances:
                    employee = attendance.employee_id

                    # Adjust check-in and check-out to the flex period
                    check_in = max(attendance.check_in, start_datetime)
                    check_out = min(attendance.check_out, end_datetime)

                    if check_in and check_out and check_in < check_out:
                        worked_hours = (check_out - check_in).total_seconds() / 3600
                        in_work_hours = employee._get_work_days_data_batch(
                            check_in, check_out, calendar=attendance.resource_calendar_id
                        )[employee.id]['hours']
                        out_work_hours = max(0, worked_hours - in_work_hours)

                        if out_work_hours > 0:
                            lines.append((0, 0, {
                                'employee_id': employee.id,
                                'overtime': out_work_hours,
                            }))

                flex.overtime_lines = lines

    def submit(self):

        users = self.env.ref('flex_overtime.group_overtime_submit').users
        if self.env.user.notification_type == 'email':
            self.env['mail.mail'].sudo().create({
                'subject': 'Overtime Submitted for Manager Line Approval',
                'body_html': 'Overtime Submitted for Manager Line Approval',
                'email_to': ','.join(map(str, users.mapped('email'))),

            })
        elif self.env.user.notification_type == 'inbox':
            # add it for activity
            for user_id in users:
                self.env['mail.activity'].sudo().create({
                    'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                    'note': 'Overtime Submitted for Manager Line Approval',
                    'res_id': self.id,
                    'res_model_id': self.env.ref('flex_overtime.model_flex_overtime').id,
                    'user_id': user_id.id,
                })




        self.filtered(lambda flex: flex.state == 'draft').write({'state': 'submit'})


    def approve_line(self):
        users = self.env.ref('flex_overtime.group_overtime_approve_line').users
        if self.env.user.notification_type == 'email':
            self.env['mail.mail'].sudo().create({
                'subject': 'Overtime Needs Your Approval',
                'body_html': 'Overtime Needs Your Approval',
                'email_to': ','.join(map(str, users.mapped('email'))),

            })
        elif self.env.user.notification_type == 'inbox':
            # add it for activity
            for user_id in users:
                self.env['mail.activity'].sudo().create({
                    'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                    'note': 'Overtime Needs Your Approval',
                    'res_id': self.id,
                    'res_model_id': self.env.ref('flex_overtime.model_flex_overtime').id,
                    'user_id': user_id.id,
                })
        self.filtered(lambda flex: flex.state == 'submit').write({'state': 'approve_line_manager'})

    def approve(self):
        self.filtered(lambda flex: flex.state == 'approve_line_manager').write({'state': 'approve'})



class FlexOverTimeLine(models.Model):
    _name = 'flex.overtime.line'

    flex_overtime_id = fields.Many2one('flex.overtime', string='Flex Overtime')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    overtime = fields.Float(string='Overtime', required=True)
