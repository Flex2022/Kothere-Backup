from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class ApprovalResignation(models.Model):
    _name = 'flex.approval.resignation'
    _description = 'Resignation Approval'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'name'

    name = fields.Char(string='Sequence', required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))
    company_id = fields.Many2one(comodel_name='res.company', required=True, index=True,
                                 default=lambda self: self.env.company)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id',
                                    readonly=True)
    resignation_date = fields.Date(string='Resignation Create Date')
    leave_date = fields.Date(string='Leave Date', required=True, default=False)
    notice_period = fields.Integer(string='Notice Period (days)', required=True)
    resignation_type = fields.Selection([
        ('resignation', 'Resignation'), ('termination', 'Termination'), ('death', 'Death')
    ], string='Resignation Type', required=True, default='resignation')
    approved_date = fields.Datetime('Resignation Approve Date', readonly=True)
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    expense_ids = fields.One2many('hr.expense', 'flex_approval_resignation_id', string='Expenses', copy=False)
    approval_request_id = fields.Many2one('approval.request', 'Approval Request', copy=False)
    types_of_end_services = fields.Selection(
        [('end_of_the_contract',
          'فسخ العقد من قبل العامل أو ترك العامل العمل لغير الحالات الواردة في المادة (81)'),
         ('employees_resignation', 'استقاله العامل (قبل انتهاء العمل)'),
         ('separation_of_the_work', 'فسخ العقد من قبل صاحب العمل لأحد الحالات الواردة في المادة (80)')],
        string='Types Of End Services', required=True)
    note = fields.Html('Note')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('direct_manager_approval', 'Waiting Direct Manager'),
        ('department_manager_approval', 'Wainting Department Manager'),
        ('hr_manager_approval', 'Waiting HR Manager'),
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
                raise ValidationError(_("Only the direct manager is authorized to approve for the employee."))

            self.write({'state': 'department_manager_approval'})

        elif self.state == 'department_manager_approval':
            # Check if the user is the department manager
            if user != self.department_id.manager_id.user_id:
                raise ValidationError(
                    _("Only the department manager is authorized to approve for the current department."))

            self.write({'state': 'hr_manager_approval'})

        elif self.state == 'hr_manager_approval':
            # Check if the user is from HR managers
            if not user.has_group('hr.group_hr_manager'):
                raise ValidationError(_("Only HR managers are authorized to approve for the HR department."))

            # Check if an approval request is associated with the resignation
            if not self.approval_request_id:
                raise ValidationError(
                    _("There is no associated termination approval request for this resignation, pls create a Termination approval "))

            # End the employee's contract by updating the contract end date
            if self.employee_id.contract_id:
                contract = self.employee_id.contract_id
                contract.write({'date_end': self.leave_date or datetime.now().date(),
                                'types_of_end_services': self.types_of_end_services})

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
                raise ValidationError(_("You can only delete records with 'Draft' or 'Rejected' state."))
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

    def action_create_termination_approval(self):
        """
        Create an approval request based on the configured approval category for resignation requests.
        """
        category_id = self.company_id.flex_employee_resignation_request_approval_type
        if not category_id:
            raise ValidationError(
                _("Please configure the approval category for resignation requests in the settings."))

        # Fetch the approval category
        approval_category = category_id

        # Create approval request
        approval_request = self.env['approval.request'].create({
            'name': approval_category.name,
            'category_id': approval_category.id,
            'request_owner_id': self.employee_id.user_id.id,
            'reason': _("Termination approval request for employee %s.") % (self.employee_id.name),
        })

        self.approval_request_id = approval_request.id

        return {
            'name': _('Termination Approval Request'),
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'approval.request',
            'res_id': approval_request.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
