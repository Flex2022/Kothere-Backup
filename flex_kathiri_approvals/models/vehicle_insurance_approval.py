from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ApprovalRenewVehicleInsurance(models.Model):
    _name = 'flex.approval.renew_vehicle_insurance'
    _description = 'Renew Vehicle Insurance Approval'
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
    department_id = fields.Many2one('hr.department', string='Department', compute="compute_related_employee_info",
                                    store=True)
    employee_job_id = fields.Many2one('hr.job', 'Job Position', compute="compute_related_employee_info", store=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True)
    last_vehicle_insurance_id = fields.Many2one('flex.approval.renew_vehicle_insurance',
                                                compute='compute_last_vehicle_insurance', store=True)
    insurance_expiry_date = fields.Date(string='Insurance Expiry Date',
                                        related="last_vehicle_insurance_id.new_insurance_end_date")

    amount = fields.Monetary("Insurance Amount", default=0.0)

    new_insurance_start_date = fields.Date(string='New Insurance Start Date', required=True)
    new_insurance_end_date = fields.Date(string='New Insurance End Date', required=True)

    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    expense_ids = fields.One2many('hr.expense', 'flex_approval_vehicle_insurance_id', string='Expenses', copy=False)
    note = fields.Html('Note')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('hr_manager_approval', 'Waiting HR Manager Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', tracking=True, copy=False)

    @api.depends('vehicle_id')
    def compute_last_vehicle_insurance(self):
        for approval in self:
            if approval.state == 'draft':
                last_insurance = self.env['flex.approval.renew_vehicle_insurance'].search([
                    ('vehicle_id', '=', approval.vehicle_id.id),
                    ('state', '=', 'approved')
                ], order='new_insurance_end_date desc', limit=1)
                approval.last_vehicle_insurance_id = last_insurance.id if last_insurance else None

    @api.depends('employee_id')
    def compute_related_employee_info(self):
        for approval in self:
            if approval.state == 'draft':
                approval.employee_number = approval.employee_id.employee_number
                approval.department_id = approval.employee_id.department_id
                approval.employee_job_id = approval.employee_id.job_id

    def action_submit_for_approval(self):
        if self.state == 'draft':
            self.write({'state': 'hr_manager_approval'})

            # make a sequence
            if self.name == _('New'):
                self.name = self.env['ir.sequence'].next_by_code('flex.approval.renew_vehicle_insurance') or _('New')

            # Notify all users with the HR Manager group
            hr_managers = self.env.ref('hr.group_hr_manager').users
            for user in hr_managers:
                self.env['bus.bus']._sendone(user.partner_id, 'simple_notification', {
                    'type': 'info',
                    'sticky': True,
                    'title': _("Approval Notification"),
                    'message': _('You have an approval notification for Renew Vehicle Insurance %s') % self.name,
                })

    def action_approve(self):
        user = self.env.user
        if self.state == 'hr_manager_approval':
            if not user.has_group('hr.group_hr_manager'):
                raise ValidationError(_("Only HR managers are authorized to approve for the HR department."))
            self.write({'state': 'approved'})

            # Notify the creator user that the vehicle insurance renewal request has been approved
            creator_user = self.create_uid
            self.env['bus.bus']._sendone(creator_user.partner_id, 'simple_notification', {
                'type': 'info',
                'sticky': True,
                'title': _("Approval Notification"),
                'message': _('Your Renew Vehicle Insurance request %s has been approved.') % self.name,
            })

            # Create an expense
            self.env['hr.expense'].create({
                'name': _('Vehicle Insurance Renewal Expense for %s') % self.employee_id.name,
                'employee_id': self.employee_id.id,
                'product_id': self.env.ref('flex_kathiri_approvals.expense_product_vehicle_insurance').id,
                'total_amount_currency': self.amount,
                'flex_approval_vehicle_insurance_id': self.id,
                'description': _('Vehicle insurance renewal expense for employee %s') % self.employee_id.name,
                'company_id': self.company_id.id,
            })

    def action_reject(self):
        return {
            'name': _('Rejection Reason'),
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'flex.approval.renew_vehicle_insurance.reject.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_renew_vehicle_insurance_id': self.id,
            },
        }

    def unlink(self):
        for approval in self:
            if approval.state not in ['draft']:
                raise models.UserError(_("You can only delete records with 'Draft' state."))
        return super(ApprovalRenewVehicleInsurance, self).unlink()

    def action_view_expenses(self):
        action = self.env.ref('hr_expense.hr_expense_actions_my_all')
        result = action.read()[0]

        if isinstance(result['context'], str):
            result['context'] = eval(result['context'])

        result['domain'] = [('flex_approval_vehicle_insurance_id', '=', self.id)]
        result['context'].update({'default_flex_approval_vehicle_insurance_id': self.id})
        return result
