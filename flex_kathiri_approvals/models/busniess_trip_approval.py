from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ApprovalBusinessTrip(models.Model):
    _name = 'flex.approval.business_trip'
    _description = 'Business Trip Approval'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'name'

    name = fields.Char(string='Sequence', required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))
    company_id = fields.Many2one(comodel_name='res.company', required=True, index=True,
                                 default=lambda self: self.env.company)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True,
                                  default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)],
                                                                                      limit=1))
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id',
                                    readonly=True)
    destination = fields.Char(string='Destination', required=True)
    purpose = fields.Char(string='Purpose', required=True)
    trip_type = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External'),
    ], string='Trip Type', required=True, default='internal')
    book_hotel = fields.Boolean('Book Hotel')
    hotel_name = fields.Char('Hotel Name')
    start_date = fields.Date(string='Start Date', required=True, default=False)
    end_date = fields.Date(string='End Date', required=True, default=False)
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    expense_ids = fields.One2many('hr.expense', 'flex_approval_business_trip_id', string='Expenses', copy=False)
    note = fields.Html('Note')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('direct_manager_approval', 'Direct Manager Approval'),
        ('department_manager_approval', 'Department Manager Approval'),
        ('hr_manager_approval', 'HR Manager Approval'),
        ('ceo_approval', 'CEO Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', tracking=True, copy=False)

    @api.model
    def create(self, vals):
        result = super(ApprovalBusinessTrip, self).create(vals)
        return result

    def action_submit_for_approval(self):
        if self.state == 'draft':
            if self.name == _('New'):
                self.name = self.env['ir.sequence'].next_by_code('flex.approval.business_trip') or _('New')
            self.write({'state': 'direct_manager_approval'})

    def action_approve_business_trip(self):
        user = self.env.user

        if self.state == 'direct_manager_approval':
            # Check if the user is the direct manager of the employee
            if user.id != self.employee_id.parent_id.user_id.id:
                raise ValidationError(
                    _("Only the direct manager (%s) is authorized to approve for the employee.")
                    % self.employee_id.parent_id.user_id.name)
            self.write({'state': 'department_manager_approval'})

        elif self.state == 'department_manager_approval':
            # Check if the user is the department manager
            if user.id != self.employee_id.department_id.manager_id.user_id.id:
                raise ValidationError(
                    _("Only the department manager (%s) is authorized to approve for the current department.")
                    % self.employee_id.department_id.manager_id.user_id.name)
            self.write({'state': 'hr_manager_approval'})

        elif self.state == 'hr_manager_approval':
            # Check if the user is from HR managers
            if not user.has_group('hr.group_hr_manager'):
                raise ValidationError(
                    _("Only HR managers are authorized to approve for the HR department."))
            self.write({'state': 'ceo_approval'})

        elif self.state == 'ceo_approval':
            # Check if the user is the CEO
            if not user.has_group('flex_kathiri_approvals.group_ceo_approval'):
                raise ValidationError(_("Only CEO is authorized to approve this."))

            # should exist expenses and all of them are  in the state done
            # Check if there are related expenses
            expenses = self.expense_ids
            if not expenses:
                raise ValidationError(_("There are no expenses related to this business trip."))

            # Check if all related expenses are in 'done' state
            if any(expense.state != 'done' for expense in expenses):
                raise ValidationError(_("All expenses related to this business trip must be in 'done' state."))

            self.write({'state': 'approved'})

    def action_reject_business_trip(self):
        return {
            'name': _('Rejection Reason'),
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'flex.approval.business_trip.reject.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_business_trip_id': self.id,
            },
        }

    def unlink(self):
        for approval in self:
            if approval.state not in ['draft', 'rejected']:
                raise models.UserError(_("You can only delete records with 'Draft' or 'Rejected' state."))
        return super(ApprovalBusinessTrip, self).unlink()

    def action_view_expenses(self):
        action = self.env.ref('hr_expense.hr_expense_actions_my_all')
        result = action.read()[0]

        # Ensure 'context' is a dictionary
        if isinstance(result['context'], str):
            result['context'] = eval(result['context'])

        result['domain'] = [('flex_approval_business_trip_id', '=', self.id)]
        result['context'].update({'default_flex_approval_business_trip_id': self.id})
        return result
