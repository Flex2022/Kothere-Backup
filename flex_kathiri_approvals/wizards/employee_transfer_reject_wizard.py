from odoo import models, fields, api, _


class ApprovalEmployeeTransferRejectWizard(models.TransientModel):
    _name = 'flex.approval.employee_transfer.reject.wizard'
    _description = 'Employee Transfer Rejection Wizard'

    reason = fields.Text(string='Rejection Reason', required=True)
    transfer_id = fields.Many2one('flex.approval.employee_transfer', string='Transfer Request')

    def action_confirm_rejection(self):
        self.transfer_id.write({
            'state': 'rejected',
        })

        # Post rejection reason in the chatter
        message = _("Transfer rejected with reason: %s") % self.reason
        self.transfer_id.message_post(body=message, message_type='comment')

        return {'type': 'ir.actions.act_window_close'}
