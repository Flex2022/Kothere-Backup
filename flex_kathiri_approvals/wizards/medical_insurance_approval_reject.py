from odoo import models, fields, api, _


class ApprovalMedicalInsuranceRejectWizard(models.TransientModel):
    _name = 'flex.approval.medical_insurance.reject.wizard'
    _description = 'Medical Insurance Rejection Wizard'

    reason = fields.Text(string='Rejection Reason', required=True)
    renew_medical_insurance_id = fields.Many2one('flex.approval.renew_medical_insurance',
                                                 string='Medical Insurance Renewal Request')

    def action_confirm_rejection(self):
        self.renew_medical_insurance_id.write({
            'state': 'rejected',
        })

        # Post rejection reason in the chatter
        message = _("Medical Insurance Renewal rejected with reason: %s") % self.reason
        self.renew_medical_insurance_id.message_post(body=message, message_type='comment')

        # Notify the creator user that the medical insurance renewal has been rejected
        creator_user = self.renew_medical_insurance_id.create_uid
        notification_message = _(
            'Your Medical Insurance Renewal request %s has been rejected.') % self.renew_medical_insurance_id.name
        self.env['bus.bus']._sendone(creator_user.partner_id, 'simple_notification', {
            'type': 'info',
            'sticky': True,
            'title': _("Rejection Notification"),
            'message': notification_message,
        })

        return {'type': 'ir.actions.act_window_close'}
