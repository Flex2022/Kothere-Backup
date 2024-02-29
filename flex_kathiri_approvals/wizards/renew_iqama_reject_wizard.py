from odoo import models, fields, api, _


class ApprovalRenewIqamaRejectWizard(models.TransientModel):
    _name = 'flex.approval.renew_iqama.reject.wizard'
    _description = 'Renew Iqama Rejection Wizard'

    reason = fields.Text(string='Rejection Reason', required=True)
    renew_iqama_id = fields.Many2one('flex.approval.renew_iqama', string='Renew Iqama Request')

    def action_confirm_rejection(self):
        self.renew_iqama_id.write({
            'state': 'rejected',
        })

        # Post rejection reason in the chatter
        message = _("Transfer rejected with reason: %s") % self.reason
        self.renew_iqama_id.message_post(body=message, message_type='comment')

        return {'type': 'ir.actions.act_window_close'}
