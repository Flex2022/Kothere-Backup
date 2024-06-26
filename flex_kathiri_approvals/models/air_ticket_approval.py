from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class FlexApprovalAirTicket(models.Model):
    _name = 'flex.approval.air_ticket'
    _description = 'Approval for Air Tickets'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'name'

    name = fields.Char(string='Number', required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))
    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)
    partner_id = fields.Many2one('res.partner', string='Beneficiary', required=True, default=lambda
        self: self.env.user.partner_id.id if self.env.user.partner_id else False)
    # department_id = fields.Many2one('hr.department', related="partner_id.department_id")
    # department_manager_id = fields.Many2one('hr.employee', related='department_id.manager_id')
    # project_id = fields.Many2one('project.project', string='Project')
    departure_city = fields.Char(string='Departure City', required=True)
    destination_city = fields.Char(string='Destination City', required=True)
    required_date = fields.Date(string='Required Date')
    request_date = fields.Date(string='Requested Date')
    # delivery_location = fields.Char(string='Delivery Location')
    recommended_supplier = fields.Many2one('res.partner', string='Recommended Supplier')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    hr_admin_note = fields.Text('HR/ADMIN Remarks', tracking=True)
    purchase_id = fields.Many2one('purchase.order')

    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    activity_ids = fields.Many2many('mail.activity')
    purchase_id = fields.Many2one('purchase.order', 'Purchase Order')
    flex_approval_exit_return_visa_id = fields.Many2one('flex.approval.exit_return_visa')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_hr_manager', 'Waiting HR Manager Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', readonly=True, copy=False, index=True, default='draft')

    def create_purchase_order(self):
        for air_ticket in self:
            if air_ticket.state != 'approved':
                raise ValidationError(_("Only approved air ticket requests can generate a purchase order."))

            purchase_order_vals = {
                'partner_id': air_ticket.recommended_supplier.id,
                'date_order': fields.Date.today(),
                'order_line': [(0, 0, {
                    'name': f'Air Ticket: {air_ticket.departure_city} to {air_ticket.destination_city}',
                    'product_id': self.env.ref('flex_kathiri_approvals.product_product_air_ticket').id,
                    'product_qty': 1,
                    'product_uom': self.env.ref('uom.product_uom_unit').id,
                    'price_unit': 0.0,  # Set your price here
                    'date_planned': air_ticket.required_date,
                })],
                'currency_id': air_ticket.currency_id.id,
                'company_id': air_ticket.company_id.id,
            }

            purchase_order = self.env['purchase.order'].sudo().create(purchase_order_vals)
            air_ticket.purchase_id = purchase_order.id
            air_ticket.message_post(body=f"Purchase order {purchase_order.name} created.")

    def action_submit_for_approval(self):
        if self.state == 'draft':
            if self.name == _('New'):
                self.name = self.env['ir.sequence'].next_by_code('flex.approval.air_ticket') or _('New')
            self.write({'state': 'waiting_hr_manager'})

            # Update the request date
            self.request_date = fields.Date.today()

            # Mark as done all previous activities
            self.make_as_done_all_activities()

            # Create an approval activity
            group = 'hr.group_hr_manager'
            user_name = self.partner_id.name
            activity_approve_message = f"Dear HR Manager,\n\n\
                                                                        Please review and approve the air ticket request submitted by {user_name}.\n\n\
                                                                        Your prompt attention to this matter is greatly appreciated.\n\n\
                                                                        Sincerely"
            activity_type = self.env.ref('flex_kathiri_approvals.mail_air_ticket_approval')
            self.create_approve_activity_for_groups(group, activity_approve_message, activity_type)

    # def action_hod_approve(self):
    #     if self.state == 'waiting_hod':
    #         # check if hod user else raise error
    #         if not (self.env.user.id == self.partner_id.department_id.manager_id.user_id.id or self.env.user.has_group(
    #                 'hr.group_hr_manager')):
    #             raise ValidationError(_("Only HOD or HR Manager can approve this."))
    #         self.write({'state': 'waiting_hr_manager''})
    #
    #         # Mark as done all previous activities
    #         self.make_as_done_all_activities()
    #
    #         # Create an approval activity
    #         group = 'flex_employee_requests.group_admin_manager'
    #         user_name = self.partner_id.name
    #         activity_approve_message = f"Dear Admin Manager,\n\n\
    #                                                         Please review and approve the air ticket request submitted by {user_name}.\n\n\
    #                                                         Your prompt attention to this matter is greatly appreciated.\n\n\
    #                                                         Sincerely"
    #         activity_type = self.env.ref('flex_employee_requests.mail_air_ticket_approval')
    #         self.create_approve_activity_for_groups(group, activity_approve_message, activity_type)

    def action_hr_manager_approve(self):
        if self.state == 'waiting_hr_manager':
            # check if hod user else raise error
            if not self.env.user.has_group('hr.group_hr_manager'):
                raise ValidationError(_("Only Admin Manager or HR Manager can approve this."))

            self.write({'state': 'approved'})

            # Mark as done all previous activities
            self.make_as_done_all_activities()

            # Send email
            template_id = self.env.ref('flex_kathiri_approvals.mail_template_air_ticket_approval',
                                       raise_if_not_found=False)
            return self.send_reminder_email(template_id)

            # self.write({'state': 'waiting_ceo_manager'})

            # # Mark as done all previous activities
            # self.make_as_done_all_activities()
            #
            # # Create an approval activity
            # group = 'flex_kathiri_approvals.group_ceo_approval'
            # user_name = self.partner_id.name
            # activity_approve_message = f"Dear CEO,\n\n\
            #                                                 Please review and approve the air ticket request submitted by {user_name}.\n\n\
            #                                                 Your prompt attention to this matter is greatly appreciated.\n\n\
            #                                                 Sincerely"
            # activity_type = self.env.ref('flex_kathiri_approvals.mail_air_ticket_approval')
            # self.create_approve_activity_for_groups(group, activity_approve_message, activity_type)

    # def action_account_dept_approve(self):
    #     if self.state == 'waiting_accounts_dept_manager':
    #         # check if hod user else raise error
    #         if not self.env.user.has_group('flex_employee_requests.group_account_dept'):
    #             raise ValidationError(_("Only Account Dept Manager can approve this."))
    #         self.write({'state': 'waiting_ceo_manager'})
    #
    #         # Mark as done all previous activities
    #         self.make_as_done_all_activities()
    #
    #         # Create an approval activity
    #         group = 'flex_employee_requests.group_ceo_approval'
    #         user_name = self.partner_id.name
    #         activity_approve_message = f"Dear CEO,\n\n\
    #                                                         Please review and approve the air ticket request submitted by {user_name}.\n\n\
    #                                                         Your prompt attention to this matter is greatly appreciated.\n\n\
    #                                                         Sincerely"
    #         activity_type = self.env.ref('flex_employee_requests.mail_air_ticket_approval')
    #         self.create_approve_activity_for_groups(group, activity_approve_message, activity_type)

    def action_ceo_approve(self):
        if self.state == 'waiting_ceo_manager':
            # check if hod user else raise error
            if not self.env.user.has_group('flex_kathiri_approvals.group_ceo_approval'):
                raise ValidationError(_("Only CEO can approve this."))
            self.write({'state': 'approved'})

            # Mark as done all previous activities
            self.make_as_done_all_activities()

            # Send email
            template_id = self.env.ref('flex_kathiri_approvals.mail_template_air_ticket_approval',
                                       raise_if_not_found=False)
            return self.send_reminder_email(template_id)

    def action_reject(self):
        return {
            'name': _('Rejection Reason'),
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'flex.approval.air_ticket.reject.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_air_ticket_id': self.id,
            },
        }

    def unlink(self):
        for approval in self:
            if approval.state not in ['draft']:
                raise models.UserError(_("You can only delete records in Draft state."))
        return super(FlexApprovalAirTicket, self).unlink()

    def create_approve_activity_for_groups(self, group, message, activity_type):
        # Get the HR manager
        user_ids = self.env.ref(group).sudo().users.filtered(lambda user: user.has_group(group))
        for user_id in user_ids:
            # Create the meeting activity for the HR manager
            self.create_approve_activity(user_id, message, activity_type)

    def create_approve_activity(self, user, summary, activity_type):
        try:
            if activity_type:
                mail_activity_id = self.env['mail.activity'].sudo().create({
                    'summary': summary,
                    'activity_type_id': activity_type.id,
                    'res_model_id': self.env['ir.model']._get('flex.approval.air_ticket').id,
                    'res_id': self.id,
                    'date_deadline': fields.Date.today() + relativedelta(days=2),
                    # Using fields.Date.today() for clarity
                    'user_id': user.id,
                })

                # Append the newly created activity to the existing activity_ids
                if mail_activity_id:
                    self.write({'activity_ids': [(4, mail_activity_id.id)]})
        except:
            pass

    def make_as_done_all_activities(self):
        """
        Mark all previous activities as done for the cash requisitions.
        """
        for requisition in self:
            # Loop through each activity associated with the cash requisition
            for activity in requisition.activity_ids:
                # Mark each activity as done
                activity.action_feedback()

    def send_reminder_email(self, mail_template):
        """ Opens a wizard to compose an email, with relevant mail template loaded by default """
        self.ensure_one()
        lang = self.env.context.get('lang')
        if mail_template:
            lang = mail_template._render_lang(self.ids)[self.id]
        ctx = {
            'default_model': 'flex.approval.air_ticket',
            'default_res_ids': self.ids,
            'default_template_id': mail_template.id if mail_template else None,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'default_email_layout_xmlid': 'mail.mail_notification_layout_with_responsible_signature',
            'force_email': True,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }
