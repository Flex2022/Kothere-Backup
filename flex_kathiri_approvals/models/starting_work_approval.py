from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ApprovalStartingWorkRequest(models.Model):
    _name = 'flex.approval.starting_work_request'
    _description = 'Starting Work Request Approval'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'name'

    def _default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    name = fields.Char(string='Sequence', required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))
    company_id = fields.Many2one(comodel_name='res.company', required=True, index=True,
                                 default=lambda self: self.env.company, string='Company')
    currency_id = fields.Many2one(
        related="company_id.currency_id", string="Currency", readonly=True, store=True, compute_sudo=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, default=_default_employee)
    employee_number = fields.Char('Employee Number', compute="compute_related_employee_info", store=True)
    iqama_id = fields.Char('Iqama ID', compute="compute_related_employee_info", store=True)
    employee_nationality = fields.Many2one('res.country', string='Nationality (country)'
                                           , compute="compute_related_employee_info", store=True)
    department_id = fields.Many2one('hr.department', string='Department', compute="compute_related_employee_info",
                                    store=True)
    employee_job_id = fields.Many2one('hr.job', 'Job Position', compute="compute_related_employee_info", store=True)
    direct_manager = fields.Many2one('hr.employee', string='Direct Manager', compute="compute_related_employee_info",
                                     store=True)
    contact_number = fields.Char(string='Contact Number', required=True)
    hod = fields.Many2one('hr.employee', string='HOD', compute="compute_related_employee_info", store=True)
    start_date = fields.Date(string='Starting Date', required=True)
    request_type = fields.Selection([
        ('enter_from_vacation', 'Enter From Vacation'),
        ('new_employee', 'New Employee')
    ], string='Request Type', required=True, default="enter_from_vacation")
    last_time_off_leave_id = fields.Many2one('hr.leave', string='Last Time Off Leave',
                                          compute="compute_employee_last_time_off_leave", store=True)
    last_time_off_leave_date_from = fields.Date(string='Last Leave Date From',
                                                related="last_time_off_leave_id.request_date_from", store=True)
    last_time_off_leave_date_to = fields.Date(string='Last Leave Date To',
                                              related="last_time_off_leave_id.request_date_to", store=True)

    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    note = fields.Html('Note')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('hr_manager_approval', 'Waiting HR Manager Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', tracking=True, copy=False)

    @api.depends('employee_id')
    def compute_employee_last_time_off_leave(self):
        for approval in self:
            if approval.employee_id:
                last_leave = self.env['hr.leave'].search([
                    ('employee_id', '=', approval.employee_id.id),
                    ('state', '=', 'validate')  # 'validate' is the state for approved leaves
                ], order='request_date_to desc', limit=1)
                approval.last_time_off_leave_id = last_leave.id if last_leave else None

    @api.depends('employee_id')
    def compute_related_employee_info(self):
        for approval in self:
            if approval.state == 'draft':
                approval.employee_number = approval.employee_id.employee_number
                approval.iqama_id = approval.employee_id.iqama_id
                approval.employee_nationality = approval.employee_id.country_id
                approval.department_id = approval.employee_id.department_id
                approval.employee_job_id = approval.employee_id.job_id
                approval.direct_manager = approval.employee_id.parent_id
                approval.hod = approval.employee_id.department_id.manager_id

    def action_submit_for_approval(self):
        if self.state == 'draft':
            self.write({'state': 'hr_manager_approval'})

            # make a sequence
            if self.name == _('New'):
                self.name = self.env['ir.sequence'].next_by_code('flex.approval.starting_work_request') or _('New')

            # Notify all users with the HR Manager group
            hr_managers = self.env.ref('hr.group_hr_manager').users
            for user in hr_managers:
                self.env['bus.bus']._sendone(user.partner_id, 'simple_notification', {
                    'type': 'info',
                    'sticky': True,
                    'title': _("Approval Notification"),
                    'message': _('You have an approval notification for Starting Work Request %s') % self.name,
                })

    def action_approve(self):
        user = self.env.user
        if self.state == 'hr_manager_approval':
            if not user.has_group('hr.group_hr_manager'):
                raise ValidationError(_("Only HR managers are authorized to approve for the HR department."))
            self.write({'state': 'approved'})

            # Notify the creator user that the starting work request has been approved
            creator_user = self.create_uid
            self.env['bus.bus']._sendone(creator_user.partner_id, 'simple_notification', {
                'type': 'info',
                'sticky': True,
                'title': _("Approval Notification"),
                'message': _('Your Starting Work Request %s has been approved.') % self.name,
            })

    def action_reject(self):
        return {
            'name': _('Rejection Reason'),
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'flex.approval.starting_work_request.reject.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_starting_work_request_id': self.id,
            },
        }

    def unlink(self):
        for approval in self:
            if approval.state not in ['draft']:
                raise models.UserError(_("You can only delete records with 'Draft' state."))
        return super(ApprovalStartingWorkRequest, self).unlink()
