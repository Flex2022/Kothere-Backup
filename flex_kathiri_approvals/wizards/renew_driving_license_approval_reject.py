from odoo import models, fields, api, _


class ApprovalRenewDrivingLicenseRejectWizard(models.TransientModel):
    _name = 'flex.approval.renew_driving_license.reject.wizard'
    _description = 'Driving License Renewal Rejection Wizard'

    renew_driving_license_id = fields.Many2one('flex.approval.renew_driving_license', string='Driving License Renewal')
    reason = fields.Text(string='Rejection Reason', required=True)

    def action_confirm_rejection(self):
        self.renew_driving_license_id.write({
            'state': 'rejected',
        })

        # Post rejection reason in the chatter
        message = _("Driving license Renewal rejected with reason: %s") % self.reason
        self.renew_driving_license_id.message_post(body=message, message_type='comment')

        # Notify the creator user that the driving license renewal has been rejected
        creator_user = self.renew_driving_license_id.create_uid
        notification_message = _(
            'Your Driving license Renewal request %s has been rejected.') % self.renew_driving_license_id.name
        self.env['bus.bus']._sendone(creator_user.partner_id, 'simple_notification', {
            'type': 'info',
            'sticky': True,
            'title': _("Rejection Notification"),
            'message': notification_message,
        })

        return {'type': 'ir.actions.act_window_close'}