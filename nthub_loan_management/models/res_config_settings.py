# -*- coding: utf-8 -*-

from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    loan_journal_id = fields.Many2one(comodel_name='account.journal',related='company_id.loan_journal_id',readonly=False, string='Journal',)
    debit_account_id = fields.Many2one(comodel_name='account.account',related='company_id.debit_account_id',readonly=False, string="Debit Account")
    credit_account_id = fields.Many2one(comodel_name='account.account',related='company_id.credit_account_id',readonly=False, string="Credit Account")


class Company(models.Model):
    _inherit = 'res.company'

    loan_journal_id = fields.Many2one(comodel_name='account.journal',string='Journal', )
    debit_account_id = fields.Many2one(comodel_name='account.account', string="Debit Account",
                                       domain="[('account_type', 'in', ('asset_receivable', 'liability_payable'))]")
    credit_account_id = fields.Many2one(comodel_name='account.account', string="Credit Account")
