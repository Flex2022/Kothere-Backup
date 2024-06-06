from odoo import models, fields, api, _


class ApprovalRenewMedicalInsurance(models.Model):
    _name = 'flex.approval.renew_medical_insurance'
    _description = 'Medical Insurance Renewal Approval'
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
    pack_id = fields.Many2one('flex.medical.insurance.pack', 'Pack', required=True)
    pack_amount = fields.Monetary("Pack Amount", default=0.0)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, default=_default_employee)
    employee_number = fields.Char('Employee Number', related="employee_id.employee_number")
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id',
                                    readonly=True)
    employee_job_id = fields.Many2one('hr.job', 'Job Position', related="employee_id.job_id")
    insurance_company_id = fields.Many2one('res.partner', "Insurance Company")

    insurance_date_from = fields.Date(string='Insurance Start Date')
    insurance_date_to = fields.Date(string='Insurance End Date')

    sponsored_ids = fields.Many2many('flex.approval.renew_medical_insurance.sponsored',
                                     relation="medical_insurance_sponsored")

    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    expense_ids = fields.One2many('hr.expense', 'flex_approval_exit_return_visa_id', string='Expenses', copy=False)
    note = fields.Html('Note')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('hr_manager_approval', 'Waiting HR Manager Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', tracking=True, copy=False)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('flex.approval.renew_medical_insurance') or _('New')
        result = super(ApprovalRenewMedicalInsurance, self).create(vals)
        return result

    @api.onchange('pack_id')
    def onchange_pack_id(self):
        for record in self:
            if record.state == 'draft':
                record.pack_amount = record.pack_id.pack_amount

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        for record in self:
            if record.state == 'draft':
                # Clear the sponsored_ids field
                record.sponsored_ids = [(5, 0, 0)]
                # Assign the related sponsored records from the employee
                if record.employee_id.medical_insurance_sponsored_ids:
                    record.sponsored_ids = [(6, 0, record.employee_id.medical_insurance_sponsored_ids.ids)]

    def action_submit_for_approval(self):
        if self.state == 'draft':
            self.write({'state': 'hr_manager_approval'})

            # make a sequence
            if self.name == _('New'):
                self.name = self.env['ir.sequence'].next_by_code('flex.approval.renew_medical_insurance') or _('New')

            # Notify all users with the HR Manager group
            hr_managers = self.env.ref('hr.group_hr_manager').users
            for user in hr_managers:
                self.env['bus.bus']._sendone(user.partner_id, 'simple_notification', {
                    'type': 'info',
                    'sticky': True,
                    'title': _("Approval Notification"),
                    'message': _('You have an approval notification for Medical Insurance Renewal %s') % self.name,
                })

    def action_approve(self):
        user = self.env.user
        if self.state == 'hr_manager_approval':
            if not user.has_group('hr.group_hr_manager'):
                raise models.ValidationError(_("Only HR managers are authorized to approve for the HR department."))
            self.write({'state': 'approved'})

            # Notify the creator user that the medical insurance has been approved
            creator_user = self.create_uid
            self.env['bus.bus']._sendone(creator_user.partner_id, 'simple_notification', {
                'type': 'info',
                'sticky': True,
                'title': _("Approval Notification"),
                'message': _('Your Medical Insurance Renewal request %s has been approved.') % self.name,
            })

            # Create an expense
            self.env['hr.expense'].create({
                'name': _('Medical Insurance Renewal Expense for %s') % self.employee_id.name,
                'employee_id': self.employee_id.id,
                'product_id': self.env.ref('flex_kathiri_approvals.expense_product_medical_insurance').id,
                'total_amount_currency': self.pack_amount,
                'flex_approval_medical_insurance_id': self.id,
                'description': _('Medical insurance renewal expense for employee %s') % self.employee_id.name,
                'company_id': self.company_id.id,
            })

    def action_reject(self):
        return {
            'name': _('Rejection Reason'),
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'flex.approval.medical_insurance.reject.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_renew_medical_insurance_id': self.id,
            },
        }

    def unlink(self):
        for approval in self:
            if approval.state not in ['draft', 'rejected']:
                raise models.UserError(_("You can only delete records with 'Draft' or 'Rejected' state."))
        return super(ApprovalRenewMedicalInsurance, self).unlink()

    def action_view_expenses(self):
        action = self.env.ref('hr_expense.hr_expense_actions_my_all')
        result = action.read()[0]

        if isinstance(result['context'], str):
            result['context'] = eval(result['context'])

        result['domain'] = [('flex_approval_medical_insurance_id', '=', self.id)]
        result['context'].update({'default_flex_approval_medical_insurance_id': self.id})
        return result


class ApprovalRenewMedicalInsuranceSponsored(models.Model):
    _name = 'flex.approval.renew_medical_insurance.sponsored'
    _description = 'Sponsored Individuals for Medical Insurance Renewal'

    employee_id = fields.Many2one('hr.employee')
    name = fields.Char(string='Name', required=True)
    relation = fields.Char(string='Relation')


class MedicalInsurancePack(models.Model):
    _name = 'flex.medical.insurance.pack'
    _description = 'Medical Insurance Package'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'name'

    name = fields.Char(string='Package Name', required=True, copy=False, readonly=False, tracking=True)
    description = fields.Text(string='Description', help='Description of the insurance package')
    company_id = fields.Many2one(comodel_name='res.company', required=True, index=True,
                                 default=lambda self: self.env.company, string='Company')
    currency_id = fields.Many2one(
        related="company_id.currency_id",
        string="Currency",
        readonly=True,
        store=True,
        compute_sudo=True,
    )
    insurance_company_id = fields.Many2one('res.partner', string='Insurance Company', required=True)
    coverage_details = fields.Html(string='Coverage Details', help='Details of the insurance coverage')
    pack_amount = fields.Monetary(string='Premium Amount', required=True, help='The amount of the insurance premium')
    coverage_limit = fields.Monetary(string='Coverage Limit', required=True,
                                     help='Maximum coverage limit of the package')
    terms_conditions = fields.Html(string='Terms and Conditions', help='Terms and conditions of the package')

    def calculate_coverage_cost(self, coverage_amount):
        """Calculates the cost of coverage based on the premium and the requested coverage amount."""
        return (coverage_amount / self.coverage_limit) * self.pack_amount

    def get_package_summary(self):
        """Provides a summary of the insurance package details."""
        summary = {
            'name': self.name,
            'description': self.description,
            'company': self.company_id.name,
            'insurance_company': self.insurance_company_id.name,
            'pack_amount': self.pack_amount,
            'coverage_limit': self.coverage_limit,
            'start_date': self.start_date,
            'end_date': self.end_date,
        }
        return summary

    def name_get(self):
        """Customize the display name of the insurance packages."""
        result = []
        for pack in self:
            name = f"{pack.name} ({pack.insurance_company_id.name})"
            result.append((pack.id, name))
        return result
