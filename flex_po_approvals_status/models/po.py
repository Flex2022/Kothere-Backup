from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PurcheseOrder(models.Model):
    _inherit = 'purchase.order'

    state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('po', 'PM Approval'),
        ('factory', 'Factory Approval'),
        ('factory_aproved', 'Financial Approval'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)

    # draft and sent
    def button_submit_to_po(self):
        self.write({'state': 'po'})

        group_approvers = self.env.ref('flex_po_approvals_status.flex_po_approvals_status_access_po_man')
        # give users if they have group sending_approvers
        if group_approvers:
            group_procurement_approvers = group_approvers.users

            # Gather their email addresses
            email_to = ','.join(user.email for user in group_procurement_approvers)
            # send email to all users have group sending_approvers
            self.env['mail.mail'].create({
                'subject': f'PO manmager Approval - Submitted, Hello please check this purchase order {self.name}, needed your approval to send it to PO Manager',
                'author_id': self.env.user.partner_id.id,
                'body_html': 'Submitted to PO Manager',
                'email_to': email_to,
            }).send()  # sent the email

    def button_submit_to_factory(self):
        self.write({'state': 'factory'})

        group_approvers = self.env.ref('flex_po_approvals_status.flex_po_approvals_status_access_fa_man')
        # give users if they have group sending_approvers
        if group_approvers:
            group_procurement_approvers = group_approvers.users

            # Gather their email addresses
            email_to = ','.join(user.email for user in group_procurement_approvers)
            # send email to all users have group sending_approvers
            self.env['mail.mail'].create({
                'subject': f'factory manmager Approval - Submitted, Hello please check this purchase order {self.name}, needed your approval to send it to factory Manager',
                'author_id': self.env.user.partner_id.id,
                'body_html': 'Submitted to factory Manager',
                'email_to': email_to,
            }).send()  # sent the email

    def button_reject_to_draft(self):
        self.write({'state': 'draft'})

        self.env['mail.mail'].create({
            'subject': f'reject from PO manager Send {self.name}',
            'author_id': self.env.user.partner_id.id,
            'body_html': 'reject from procurement',
            'email_to': self.user_id.email,
        }).send()  # sent the email

    def button_submit_to_financial(self):
        self.write({'state': 'factory_aproved'})

        group_approvers = self.env.ref('flex_po_approvals_status.flex_po_approvals_status_access_fin_man')
        # give users if they have group sending_approvers
        if group_approvers:
            group_procurement_approvers = group_approvers.users

            # Gather their email addresses
            email_to = ','.join(user.email for user in group_procurement_approvers)
            # send email to all users have group sending_approvers
            self.env['mail.mail'].create({
                'subject': f'Financial Approval - Submitted, Hello please check this purchase order {self.name}, needed your approval to send it to Financial Manager',
                'author_id': self.env.user.partner_id.id,
                'body_html': 'Submitted to factory Manager',
                'email_to': email_to,
            }).send()  # sent the email

    def button_reject_to_po(self):
        self.write({'state': 'po'})

        self.env['mail.mail'].create({
            'subject': f'reject from factory manager Send {self.name}',
            'author_id': self.env.user.partner_id.id,
            'body_html': 'reject from factory',
            'email_to': self.user_id.email,
        }).send()  # sent the email

    def button_reject_to_factory(self):
        self.write({'state': 'factory'})

        self.env['mail.mail'].create({
            'subject': f'reject from Financial manager Send {self.name}',
            'author_id': self.env.user.partner_id.id,
            'body_html': 'reject from Financial',
            'email_to': self.user_id.email,
        }).send()  # sent the email

    def button_confirm(self):
        for order in self:
            if order.state not in ['factory_aproved', 'to approve']:
                continue
            order.order_line._validate_analytic_distribution()
            order._add_supplier_to_product()
            # Deal with double validation process
            if order._approval_allowed():
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        return True

    def write(self, vals):
        if self.state == 'draft':
            return super(PurcheseOrder, self).write(vals)
        else:
            if self.env.user.has_group('flex_po_approvals_status.flex_po_approvals_status_access_fin_man'):
                return super(PurcheseOrder, self).write(vals)
            else:
                if len(list(vals.keys())) == 1:
                    if 'state' in list(vals.keys()):
                        return super(PurcheseOrder, self).write(vals)
                    else:
                        raise UserError(
                            _('You can not edit this record on this state, please return to RFQ state, then edit it'))
                else:
                    raise UserError(
                        _('You can not edit this record on this state, please return to RFQ state, then edit it'))
