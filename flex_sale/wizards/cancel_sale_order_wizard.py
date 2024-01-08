# wizard_cancel_reason.py

from odoo import models, fields, api, _


class SaleOrderCancelReasonWizard(models.TransientModel):
    _name = 'sale.order.cancel.reason.wizard'
    _description = 'Sale Order Cancel Reason Wizard'

    order_id = fields.Many2one('sale.order')
    cancel_reason = fields.Text(string='Cancellation Reason', required=True)

    def submit_cancel_reason(self):
        # Update the sale order state to 'cancel'
        self.order_id.state = 'cancel'

        # Post the cancellation reason on the chatter
        subject = _('Cancellation Reason')
        body = _('Cancellation Reason: "%s"', self.cancel_reason)
        self.order_id.message_post(subject=subject, body=body, author_id=self.env.user.partner_id.id)

        return {'type': 'ir.actions.act_window_close'}

