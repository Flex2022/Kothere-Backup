from odoo import models, fields, api, _


class ApprovalAirTicketRejectWizard(models.TransientModel):
    _name = 'flex.approval.air_ticket.reject.wizard'
    _description = 'Air Ticket Rejection Wizard'

    reason = fields.Text(string='Rejection Reason', required=True)
    air_ticket_id = fields.Many2one('flex.approval.air_ticket', string='Air Ticket Request')

    def action_confirm_rejection(self):
        self.air_ticket_id.write({
            'state': 'rejected',
        })
        # Post rejection reason in the chatter
        message = _("This Air ticket rejected with reason: %s") % self.reason
        self.air_ticket_id.message_post(body=message, message_type='comment')
        # Send rejection email
        template_id = self.env.ref('flex_kathiri_approvals.mail_template_air_ticket_approval',
                                   raise_if_not_found=False)
        return self.send_reminder_email(template_id)

    def send_reminder_email(self, mail_template):
        """ Opens a wizard to compose an email, with relevant mail template loaded by default """
        self.ensure_one()
        lang = self.env.context.get('lang')
        if mail_template:
            lang = mail_template._render_lang(self.ids)[self.id]
        ctx = {
            'default_model': 'flex.approval.air_ticket',
            'default_res_ids': self.air_ticket_id.ids,
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
