from odoo import models, fields, api, _


class ApprovalResignation(models.Model):
    _name = 'flex.approval.resignation'
    _description = 'Resignation Approval'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'name'

    name = fields.Char(string='Sequence', required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id',
                                    readonly=True)
    resignation_date = fields.Date(string='Resignation Date')
    leave_date = fields.Date(string='Leave Date', required=True, default=False)
    notice_period = fields.Integer(string='Notice Period (days)', required=True)
    resignation_type = fields.Selection([
        ('resignation', 'Resignation'), ('termination', 'Termination'), ('death', 'Death')
    ], string='Resignation Type', required=True, default='resignation')
    approved_date = fields.Datetime('Resignation Approve Date', readonly=True)
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    expense_ids = fields.One2many('hr.expense', 'flex_approval_resignation_id', string='Expenses', copy=False)
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
            vals['name'] = self.env['ir.sequence'].next_by_code('flex.approval.resignation') or _('New')
        result = super(ApprovalResignation, self).create(vals)
        return result

    def action_submit_for_approval(self):
        self.write({'state': 'direct_manager_approval', 'resignation_date': fields.Date.today()})

    def action_approve_resignation(self):
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

    def action_reject_resignation(self):
        return {
            'name': _('Rejection Reason'),
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'flex.approval.resignation.reject.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_resignation_id': self.id,
            },
        }

    def unlink(self):
        for approval in self:
            if approval.state not in ['draft', 'rejected']:
                raise models.UserError(_("You can only delete records with 'Draft' or 'Rejected' state."))
        return super(ApprovalResignation, self).unlink()

    def action_view_expenses(self):
        action = self.env.ref('hr_expense.hr_expense_actions_my_all')
        result = action.read()[0]

        # Ensure 'context' is a dictionary
        if isinstance(result['context'], str):
            result['context'] = eval(result['context'])

        result['domain'] = [('flex_approval_resignation_id', '=', self.id)]
        result['context'].update({'default_flex_approval_resignation_id': self.id})
        return result