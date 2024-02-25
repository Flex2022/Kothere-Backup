from odoo import models, fields, api, _


class ApprovalRenewIqama(models.Model):
    _name = 'flex.approval.renew_iqama'
    _description = 'Iqama Renewal Approval'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'name'

    def _default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    name = fields.Char(string='Sequence', required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True,
                                  default=_default_employee)
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id',
                                    readonly=True)
    current_iqama_id = fields.Char(string='Current Iqama ID', related='employee_id.iqama_id', readonly=True)
    end_of_iqama = fields.Date(string='Current Expiry Date', related='employee_id.end_of_iqama', readonly=True)
    new_iqama_id = fields.Char(string='New Iqama ID', required=True)
    renewal_date = fields.Date(string='New Expiry Date', required=True, default=False)
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    note = fields.Html('Note')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('direct_manager_approval', 'Direct Manager Approval'),
        ('department_manager_approval', 'Department Manager Approval'),
        ('hr_manager_approval', 'HR Manager Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', tracking=True, copy=False)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('flex.approval.renew_iqama') or _('New')
        result = super(ApprovalRenewIqama, self).create(vals)
        return result

    def action_submit_for_approval(self):
        if self.state == 'draft':
            self.write({'state': 'direct_manager_approval'})

    def action_approve_renewal(self):
        user = self.env.user

        if self.state == 'direct_manager_approval':
            # Check if the user is the direct manager of the employee
            if user != self.employee_id.parent_id.user_id:
                raise models.ValidationError(_("Only the direct manager is authorized to approve for the employee."))

            self.write({'state': 'department_manager_approval'})

        elif self.state == 'department_manager_approval':
            # Check if the user is the department manager
            if user != self.department_id.manager_id.user_id:
                raise models.ValidationError(
                    _("Only the department manager is authorized to approve for the current department."))

            self.write({'state': 'hr_manager_approval'})

        elif self.state == 'hr_manager_approval':
            # Check if the user is from HR managers
            if not user.has_group('hr.group_hr_manager'):
                raise models.ValidationError(_("Only HR managers are authorized to approve for the HR department."))

            self.write({'state': 'approved'})
            self.employee_id.iqama_id = self.new_iqama_id
            self.employee_id.renewal_date = self.renewal_date

    def action_reject_renewal(self):
        return {
            'name': _('Rejection Reason'),
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'flex.approval.renew_iqama.reject.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_renew_iqama_id': self.id,
            },
        }

    def unlink(self):
        for approval in self:
            if approval.state not in ['draft', 'rejected']:
                raise models.UserError(_("You can only delete records with 'Draft' or 'Rejected' state."))
        return super(ApprovalRenewIqama, self).unlink()
