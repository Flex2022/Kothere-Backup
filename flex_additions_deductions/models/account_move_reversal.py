# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError


class AccountMoveReversal(models.TransientModel):
    """
    Account move reversal wizard, it cancel an account move by reversing it.
    """
    _inherit = 'account.move.reversal'

    def _prepare_default_reversal(self, move):
        reverse_date = self.date
        mixed_payment_term = move.invoice_payment_term_id.id if move.invoice_payment_term_id.early_pay_discount_computation == 'mixed' else None
        return {
            'ref': _('Reversal of: %(move_name)s, %(reason)s', move_name=move.name, reason=self.reason)
            if self.reason
            else _('Reversal of: %s', move.name),
            'date': reverse_date,
            'invoice_date_due': reverse_date,
            'invoice_date': move.is_invoice(include_receipts=True) and (self.date or move.date) or False,
            'journal_id': self.journal_id.id,
            'invoice_payment_term_id': mixed_payment_term,
            'invoice_user_id': move.invoice_user_id.id,
            'auto_post': 'at_date' if reverse_date > fields.Date.context_today(self) else 'no',
            'flex_deductions_ids': [(0, 0, {
                'name': line.name,
                'deductions_id': line.deductions_id.id,
                'amount_deductions': line.amount_deductions,
                'is_percentage': line.is_percentage,
                'percentage_or_value': line.percentage_or_value,
                'tax_id': line.tax_id.id,
            }) for line in move.flex_deductions_ids],
            'flex_additions_ids': [(0, 0, {
                'name': line.name,
                'additions_id': line.additions_id.id,
                'amount_deductions': line.amount_deductions,
                'is_percentage': line.is_percentage,
                'percentage_or_value': line.percentage_or_value,
                'tax_id': line.tax_id.id,
            }) for line in move.flex_additions_ids],
        }