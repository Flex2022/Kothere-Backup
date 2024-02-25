from odoo import models, fields, api, _


class ApprovalResignationRejectWizard(models.TransientModel):
    _name = 'flex.approval.resignation.reject.wizard'
    _description = 'Resignation Rejection Wizard'

    reason = fields.Text(string='Rejection Reason', required=True)
    resignation_id = fields.Many2one('flex.approval.resignation', string='Resignation Request')

    def action_confirm_rejection(self):
        self.resignation_id.write({
            'state': 'rejected',
        })

        # Post rejection reason in the chatter
        message = _("Transfer rejected with reason: %s") % self.reason
        self.resignation_id.message_post(body=message, message_type='comment')

        return {'type': 'ir.actions.act_window_close'}
