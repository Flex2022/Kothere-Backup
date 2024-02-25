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
        ('current_department_approval', 'Current Department Approval'),
        ('employee_approval', 'Employee Approval'),
        ('hr_approval', 'HR Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', tracking=True, copy=False)

    # Optional: Add a responsible user/manager field for approval
    # responsible_user_id = fields.Many2one('res.users', string='Responsible User', help="User responsible for approving the transfer.")

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('flex.approval.employee_transfer') or _('New')
        result = super(ApprovalEmployeeTransfer, self).create(vals)
        return result

    def action_submit_for_approval(self):
        if self.current_department_id == self.new_department_id:
            raise models.ValidationError(_("Current and new departments must not be the same."))
        self.write({'state': 'current_department_approval'})

    def action_approve_transfer(self):
        user = self.env.user

        if self.state == 'current_department_approval':
            # Check if the user is the manager of the current department
            if user != self.current_department_id.manager_id:
                raise models.ValidationError(
                    _("Only the department manager is authorized to approve the transfer for the current department."))

            self.write({'state': 'employee_approval'})

        elif self.state == 'employee_approval':
            # Check if the user is the employee
            if user != self.employee_id.user_id:
                raise models.ValidationError(
                    _("Only the employee is authorized to approve the transfer for the current department."))

            self.write({'state': 'hr_approval'})

        elif self.state == 'hr_approval':
            # Check if the user is the HR manager
            if user not in self.env.ref('hr.group_hr_manager').sudo().users:
                raise models.ValidationError(
                    _("Only the HR managers are authorized to approve the transfer for the employee."))

            self.write({'state': 'approved'})
            self.employee_id.department_id = self.new_department_id

    def action_reject_transfer(self):
        return {
            'name': _('Rejection Reason'),
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'flex.approval.employee_transfer.reject.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_transfer_id': self.id,
            },
        }

    def unlink(self):
        for approval in self:
            if approval.state not in ['draft', 'rejected']:
                raise models.UserError(_("You can only delete records with 'Draft' or 'Rejected' state."))
        return super(ApprovalEmployeeTransfer, self).unlink()
