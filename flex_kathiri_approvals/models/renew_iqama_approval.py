from odoo import models, fields, api, _
from datetime import timedelta


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
    company_id = fields.Many2one(comodel_name='res.company', required=True, index=True,
                                 default=lambda self: self.env.company)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True,
                                  default=_default_employee)
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id',
                                    readonly=True)
    current_iqama_id = fields.Char(string='Current Iqama ID', compute='compute_current_current_iqama_id', store=True)
    end_of_iqama = fields.Date(string='Current Expiry Date', compute='compute_current_current_iqama_id', store=True)
    new_iqama_id = fields.Char(string='New Iqama ID')
    renewal_start_date = fields.Date(string='Renewal Starting Date')
    renewal_period = fields.Selection(
        [('three_months', '3 Months'), ('six_months', 'Six Months'), ('nine_months', 'Nine Months'),
         ('one_year', 'One Year')], string="Renewal period")
    renewal_date = fields.Date(string='New Expiry Date', compute='compute_renewal_period')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    expense_ids = fields.One2many('hr.expense', 'flex_approval_iqama_id', string='Expenses', copy=False)
    note = fields.Html('Note')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('direct_manager_approval', 'Direct Manager Approval'),
        ('department_manager_approval', 'Manager Approval'),
        ('hr_manager_approval', 'HR Manager Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', tracking=True, copy=False)

    @api.depends('end_of_iqama', 'renewal_period')
    def compute_renewal_period(self):
        for approval in self:
            approval.renewal_date = False
            if approval.renewal_period and approval.end_of_iqama:
                if approval.renewal_period == 'three_months':
                    approval.renewal_date = approval.end_of_iqama + timedelta(days=90)
                elif approval.renewal_period == 'six_months':
                    approval.renewal_date = approval.end_of_iqama + timedelta(days=180)
                elif approval.renewal_period == 'nine_months':
                    approval.renewal_date = approval.end_of_iqama + timedelta(days=270)
                elif approval.renewal_period == 'one_year':
                    approval.renewal_date = approval.end_of_iqama + timedelta(days=365)
            elif approval.renewal_period and approval.renewal_start_date and not approval.end_of_iqama:
                if approval.renewal_period == 'three_months':
                    approval.renewal_date = approval.renewal_start_date + timedelta(days=90)
                elif approval.renewal_period == 'six_months':
                    approval.renewal_date = approval.renewal_start_date + timedelta(days=180)
                elif approval.renewal_period == 'nine_months':
                    approval.renewal_date = approval.renewal_start_date + timedelta(days=270)
                elif approval.renewal_period == 'one_year':
                    approval.renewal_date = approval.renewal_start_date + timedelta(days=365)

    @api.depends('employee_id')
    def compute_current_current_iqama_id(self):
        for approval in self:
            if approval.state == 'draft':
                approval.current_iqama_id = approval.employee_id.iqama_id.id
                approval.end_of_iqama = approval.employee_id.end_of_iqama

    @api.model
    def create(self, vals):
        result = super(ApprovalRenewIqama, self).create(vals)
        return result

    def action_submit_for_approval(self):
        if self.state == 'draft':
            if self.name == _('New'):
                self.name = self.env['ir.sequence'].next_by_code('flex.approval.renew_iqama') or _('New')
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
            self.employee_id.end_of_iqama = self.renewal_date

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

    def action_view_expenses(self):
        action = self.env.ref('hr_expense.hr_expense_actions_my_all')
        result = action.read()[0]

        # Ensure 'context' is a dictionary
        if isinstance(result['context'], str):
            result['context'] = eval(result['context'])

        result['domain'] = [('flex_approval_iqama_id', '=', self.id)]
        result['context'].update({'default_flex_approval_iqama_id': self.id})
        return result
