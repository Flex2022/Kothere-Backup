from odoo import models, fields, api, _


class ApprovalExitReturnVisaRejectWizard(models.TransientModel):
    _name = 'flex.approval.exit_return_visa.reject.wizard'
    _description = 'Exit Return Visa Rejection Wizard'

    reason = fields.Text(string='Rejection Reason', required=True)
    exit_return_visa_id = fields.Many2one('flex.approval.exit_return_visa',
                                                 string='Exit Return Visa Request')

    def action_confirm_rejection(self):
        self.exit_return_visa_id.write({
            'state': 'rejected',
        })

        # Post rejection reason in the chatter
        message = _("Exit Return Visa rejected with reason: %s") % self.reason
        self.exit_return_visa_id.message_post(body=message, message_type='comment')

        # Notify the creator user that the Exit Return Visa has been rejected
        creator_user = self.exit_return_visa_id.create_uid
        notification_message = _(
            'Your Exit Return Visa request %s has been rejected.') % self.exit_return_visa_id.name
        self.env['bus.bus']._sendone(creator_user.partner_id, 'simple_notification', {
            'type': 'info',
            'sticky': True,
            'title': _("Rejection Notification"),
            'message': notification_message,
        })

        return {'type': 'ir.actions.act_window_close'}
