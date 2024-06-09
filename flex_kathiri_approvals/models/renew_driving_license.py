from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ApprovalRenewDrivingLicense(models.Model):
    _name = 'flex.approval.renew_driving_license'
    _description = 'Driving license Renewal Approval'
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
    employee_number = fields.Char('Employee Number', related="employee_id.employee_number")
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id',
                                    readonly=True)
    employee_job_id = fields.Many2one('hr.job', 'Job Position', related="employee_id.job_id")
    # driving_license_number = fields.Char('Driving license Number', required=True)
    driving_license_date_from = fields.Date(string='License Start Date', required=True)
    driving_license_date_to = fields.Date(string='License End Date', required=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string='Assigned Vehicle', required=True)
    last_vehicle_license_id = fields.Many2one('flex.approval.renew_driving_license',
                                              string='Last Approved Vehicle Driving license',
                                              compute='_compute_last_vehicle_license', store=True, readonly=True)
    last_driving_license_date_from = fields.Date(string='Last License Start Date',
                                                 related="last_vehicle_license_id.driving_license_date_from")
    last_driving_license_date_to = fields.Date(string='Last License End Date',
                                               related="last_vehicle_license_id.driving_license_date_to")

    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    expense_ids = fields.One2many('hr.expense', 'flex_approval_renew_driving_license_id', string='Expenses', copy=False)
    note = fields.Html('Note')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('hr_manager_approval', 'Waiting HR Manager Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', tracking=True, copy=False)

    @api.depends('vehicle_id')
    def _compute_last_vehicle_license(self):
        for record in self:
            if record.state == 'draft':
                if record.vehicle_id:
                    last_license = self.search([
                        ('vehicle_id', '=', record.vehicle_id.id),
                        ('state', '=', 'approved')
                    ], order='driving_license_date_to desc', limit=1)
                    record.last_vehicle_license_id = last_license.id if last_license else False
                else:
                    record.last_vehicle_license_id = False

    @api.constrains('driving_license_date_from', 'driving_license_date_to', 'vehicle_id')
    def _check_driving_license_dates(self):
        for record in self:
            if record.vehicle_id and record.state == 'draft':
                last_license = record.last_vehicle_license_id
                if last_license and (record.driving_license_date_from <= last_license.driving_license_date_to):
                    raise ValidationError(
                        _("The new driving license dates must be later than the last approved driving license dates for this vehicle."))


    def action_submit_for_approval(self):
        if self.state == 'draft':
            self.write({'state': 'hr_manager_approval'})

            # make a sequence
            if self.name == _('New'):
                self.name = self.env['ir.sequence'].next_by_code('flex.approval.renew_driving_license') or _('New')

            # Notify all users with the HR Manager group
            hr_managers = self.env.ref('hr.group_hr_manager').users
            for user in hr_managers:
                self.env['bus.bus']._sendone(user.partner_id, 'simple_notification', {
                    'type': 'info',
                    'sticky': True,
                    'title': _("Approval Notification"),
                    'message': _('You have an approval notification for Driving license Renewal %s') % self.name,
                })

    def action_approve(self):
        user = self.env.user
        if self.state == 'hr_manager_approval':
            if not user.has_group('hr.group_hr_manager'):
                raise models.ValidationError(_("Only HR managers are authorized to approve for the HR department."))
            self.write({'state': 'approved'})

            # Notify the creator user that the driving license renewal has been approved
            creator_user = self.create_uid
            self.env['bus.bus']._sendone(creator_user.partner_id, 'simple_notification', {
                'type': 'info',
                'sticky': True,
                'title': _("Approval Notification"),
                'message': _('Your Driving license Renewal request %s has been approved.') % self.name,
            })

            # Create an expense
            self.env['hr.expense'].create({
                'name': _('Driving license Renewal Expense for %s') % self.employee_id.name,
                'employee_id': self.employee_id.id,
                'product_id': self.env.ref('flex_kathiri_approvals.expense_product_driving_license').id,
                'total_amount_currency': self.env['ir.config_parameter'].sudo().get_param(
                    'driving_license_renewal_cost', 0.0),
                'flex_approval_renew_driving_license_id': self.id,
                'description': _('Driving license renewal expense for employee %s') % self.employee_id.name,
                'company_id': self.company_id.id,
            })

    def action_reject(self):
        return {
            'name': _('Rejection Reason'),
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'flex.approval.renew_driving_license.reject.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_renew_driving_license_id': self.id,
            },
        }

    def unlink(self):
        for approval in self:
            if approval.state not in ['draft']:
                raise models.UserError(_("You can only delete records with 'Draft' state."))
        return super(ApprovalRenewDrivingLicense, self).unlink()

    def action_view_expenses(self):
        action = self.env.ref('hr_expense.hr_expense_actions_my_all')
        result = action.read()[0]

        if isinstance(result['context'], str):
            result['context'] = eval(result['context'])

        result['domain'] = [('flex_approval_renew_driving_license_id', '=', self.id)]
        result['context'].update({'default_flex_approval_renew_driving_license_id': self.id})
        return result
