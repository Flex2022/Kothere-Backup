from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ExitReturnVisa(models.Model):
    _name = 'flex.approval.exit_return_visa'
    _description = 'Exit Return Visa'
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
    employee_nationality = fields.Many2one('res.country', string='Nationality (country)',
                                           related="employee_id.country_id")
    employee_number = fields.Char('Employee Number', related="employee_id.employee_number")
    employee_job_id = fields.Many2one('hr.job', 'Job Position', related="employee_id.job_id")
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id',
                                    readonly=True)
    visa_for = fields.Selection([('vacation', 'Vacation'), ('mission', 'Mission')], string='Visa For',
                                default="vacation")
    visa_date_from = fields.Date(string='Visa Start Date')
    visa_date_to = fields.Date(string='Visa End Date')
    visa_amount = fields.Monetary("Visa Amount", default=0.0)
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    # expense_ids = fields.One2many('hr.expense', 'flex_approval_medical_insurance_id', string='Expenses', copy=False)
    leave_id = fields.Many2one('hr.leave')
    note = fields.Html('Note')
    sponsored_ids = fields.Many2many('flex.approval.renew_medical_insurance.sponsored',
                                     relation="exit_return_visa_sponsored")
    air_ticket_ids = fields.One2many('flex.approval.air_ticket', 'flex_approval_exit_return_visa_id')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('hr_manager_approval', 'Waiting HR Manager Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', tracking=True, copy=False)

    def action_create_air_ticket(self):
        AirTicket = self.env['flex.approval.air_ticket']

        for visa_approval in self:
            if visa_approval.state != 'approved':
                raise ValidationError(_('You cannot create an air ticket for unapproved visas.'))

            lst_partners = [visa_approval.employee_id.work_contact_id] + [sponsored.partner_id for sponsored in
                                                                             self.sponsored_ids]
            for partner in lst_partners:
                # Create Air Ticket record
                air_ticket_vals = {
                    'date_from': visa_approval.visa_date_from,
                    'date_to': visa_approval.visa_date_to,
                    'partner_id': partner.id,
                    'flex_approval_exit_return_visa_id': visa_approval.id,
                    'departure_city': '.',
                    'destination_city': '.',
                    'company_id': visa_approval.company_id.id,
                    'state': 'draft',
                }
                created_ticket = AirTicket.create(air_ticket_vals)

            # Perform additional actions or validations as needed
            hr_managers = self.env.ref('hr.group_hr_manager').users
            for user in hr_managers:
                self.env['bus.bus']._sendone(user.partner_id, 'simple_notification', {
                    'type': 'info',
                    'sticky': True,
                    'title': _("Air Ticket Created"),
                    'message': _('An air ticket has been created for Exit Return Visa %s') % visa_approval.name,
                })

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        for record in self:
            if record.state == 'draft':
                # Clear the sponsored_ids field
                record.sponsored_ids = [(5, 0, 0)]
                # Assign the related sponsored records from the employee
                if record.employee_id.medical_insurance_sponsored_ids:
                    record.sponsored_ids = [(6, 0, record.employee_id.medical_insurance_sponsored_ids.ids)]

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        for record in self:
            if record.state == 'draft':
                # Clear the related fields
                record.department_id = record.employee_id.department_id
                record.employee_job_id = record.employee_id.job_id

    def action_submit_for_approval(self):
        if self.state == 'draft':

            # make sure there are <= 2 sponsored
            if len(self.sponsored_ids) > 2:
                raise ValidationError(_("Cannot submit for approval: Maximum 2 sponsored allowed."))

            self.write({'state': 'hr_manager_approval'})

            # make a sequence
            if self.name == _('New'):
                self.name = self.env['ir.sequence'].next_by_code('exit.return.visa') or _('New')

            # Notify all users with the HR Manager group
            hr_managers = self.env.ref('hr.group_hr_manager').users
            for user in hr_managers:
                self.env['bus.bus']._sendone(user.partner_id, 'simple_notification', {
                    'type': 'info',
                    'sticky': True,
                    'title': _("Approval Notification"),
                    'message': _('You have an approval notification for Exit Return Visa %s') % self.name,
                })

    def action_approve(self):
        user = self.env.user
        if self.state == 'hr_manager_approval':
            if not user.has_group('hr.group_hr_manager'):
                raise models.ValidationError(_("Only HR managers are authorized to approve for the HR department."))
            self.write({'state': 'approved'})

            # Notify the creator user that the exit return visa has been approved
            creator_user = self.create_uid
            self.env['bus.bus']._sendone(creator_user.partner_id, 'simple_notification', {
                'type': 'info',
                'sticky': True,
                'title': _("Approval Notification"),
                'message': _('Your Exit Return Visa request %s has been approved.') % self.name,
            })
            # # Create an expense
            # hr_expense_id = self.env['hr.expense'].sudo().create({
            #     'name': _('Exit Return Visa Expense for %s') % self.employee_id.name,
            #     'employee_id': self.employee_id.id,
            #     'product_id': self.env.ref('flex_kathiri_approvals.expense_product_visa').id,
            #     'total_amount_currency': self.visa_amount,
            #     'flex_approval_exit_return_visa_id': self.id,
            #     'description': _('Exit return visa expense for employee %s') % self.employee_id.name,
            #     'company_id': self.company_id.id,
            # })
            # hr_expense_id

    def action_reject(self):
        return {
            'name': _('Rejection Reason'),
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'flex.approval.exit_return_visa.reject.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_exit_return_visa_id': self.id,
            },
        }

    def unlink(self):
        for visa in self:
            if visa.state not in ['draft', 'rejected']:
                raise models.UserError(_("You can only delete records with 'Draft' or 'Rejected' state."))
        return super(ExitReturnVisa, self).unlink()

    # def action_view_expenses(self):
    #     action = self.env.ref('hr_expense.hr_expense_actions_my_all')
    #     result = action.read()[0]
    #
    #     if isinstance(result['context'], str):
    #         result['context'] = eval(result['context'])
    #
    #     result['domain'] = [('flex_approval_exit_return_visa_id', '=', self.id)]
    #     result['context'].update({'default_flex_approval_exit_return_visa_id': self.id})
    #     return result



    def action_view_air_tickets(self):
        action = self.env.ref('flex_kathiri_approvals.action_approval_air_ticket')
        result = action.read()[0]

        if isinstance(result['context'], str):
            result['context'] = eval(result['context'])

        result['domain'] = [('flex_approval_exit_return_visa_id', '=', self.id)]
        result['context'].update({'default_flex_approval_exit_return_visa_id': self.id})
        return result
