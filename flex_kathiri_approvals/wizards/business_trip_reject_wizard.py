from odoo import models, fields, api, _


class ApprovalBusinessTripRejectWizard(models.TransientModel):
    _name = 'flex.approval.business_trip.reject.wizard'
    _description = 'Business Trip Rejection Wizard'

    reason = fields.Text(string='Rejection Reason', required=True)
    business_trip_id = fields.Many2one('flex.approval.business_trip', string='Business Trip Request')

    def action_confirm_rejection(self):
        self.business_trip_id.write({
            'state': 'rejected',
        })

        # Post rejection reason in the chatter
        message = _("Transfer rejected with reason: %s") % self.reason
        self.business_trip_id.message_post(body=message, message_type='comment')

        return {'type': 'ir.actions.act_window_close'}
