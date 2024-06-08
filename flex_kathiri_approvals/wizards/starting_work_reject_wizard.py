from odoo import models, fields, api, _

class ApprovalStartingWorkRequestRejectWizard(models.TransientModel):
    _name = 'flex.approval.starting_work_request.reject.wizard'
    _description = 'Starting Work Request Rejection Wizard'

    reason = fields.Text(string='Rejection Reason', required=True)
    starting_work_request_id = fields.Many2one('flex.approval.starting_work_request',
                                               string='Starting Work Request')

    def action_confirm_rejection(self):
        self.starting_work_request_id.write({
            'state': 'rejected',
        })

        # Post rejection reason in the chatter
        message = _("Starting Work Request rejected with reason: %s") % self.reason
        self.starting_work_request_id.message_post(body=message, message_type='comment')

        # Notify the creator user that the starting work request has been rejected
        creator_user = self.starting_work_request_id.create_uid
        notification_message = _(
            'Your Starting Work Request %s has been rejected.') % self.starting_work_request_id.name
        self.env['bus.bus']._sendone(creator_user.partner_id, 'simple_notification', {
            'type': 'info',
            'sticky': True,
            'title': _("Rejection Notification"),
            'message': notification_message,
        })

        return {'type': 'ir.actions.act_window_close'}
