from odoo import models, fields, api, _


class ApprovalEmployeeTransfer(models.Model):
    _name = 'flex.approval.employee_transfer'
    _description = 'Employee Transfer Approval'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'name'

    name = fields.Char(string='Transfer Request', required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    current_department_id = fields.Many2one('hr.department', string='Current Department',
                                            related='employee_id.department_id', readonly=True)
    new_department_id = fields.Many2one('hr.department', string='New Department', required=True)

    transfer_reason = fields.Html(string='Transfer Reason', required=True)
    transfer_date = fields.Date(string='Transfer Date', required=True, default=fields.Date.today())
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('new_department_approval', 'New Department Approval'),
        ('current_department_approval', 'Current Department Approval'),
        ('employee_approval', 'Employee Approval'),
        ('hr_approval', 'HR Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', track_visibility='onchange', copy=False)

    # Optional: Add a responsible user/manager field for approval
    # responsible_user_id = fields.Many2one('res.users', string='Responsible User', help="User responsible for approving the transfer.")

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('flex.approval.employee_transfer') or _('New')
        result = super(ApprovalEmployeeTransfer, self).create(vals)
        return result

    def action_submit_for_approval(self):
        self.write({'state': 'new_department_approval'})

    def action_approve_transfer(self):
        if self.state == 'new_department_approval':
            self.write({'state': 'current_department_approval'})
        elif self.state == 'current_department_approval':
            self.write({'state': 'employee_approval'})
        elif self.state == 'employee_approval':
            self.write({'state': 'hr_approval'})
        elif self.state == 'hr_approval':
            self.write({'state': 'approved'})

    def action_reject_transfer(self):
        self.write({'state': 'rejected'})


