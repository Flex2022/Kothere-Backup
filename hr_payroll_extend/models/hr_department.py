# -*- coding: utf-8 -*-

from odoo import models, fields


class Department(models.Model):
    _inherit = 'hr.department'

    journal_id = fields.Many2one('account.journal', 'Journal')
    salary_account_id = fields.Many2one('account.account', 'Salary Account')
    increase_account_id = fields.Many2one('account.account', 'Variable Increase Account')
    basic_account_id = fields.Many2one('account.account', 'Basic Account')
    housing_account_id = fields.Many2one('account.account', 'Housing Account')
    Transportation_account_id = fields.Many2one('account.account', 'Transportation Account')
    eos_account_id = fields.Many2one('account.account', 'EOS Account')
    leave_account_id = fields.Many2one('account.account', 'Leaves Account')
    ticket_account_id = fields.Many2one('account.account', 'Ticket Account')
    overtime_account_id = fields.Many2one('account.account', 'Overtime Account')
    other_account_id = fields.Many2one('account.account', 'Other Account')
    per_diem_account_id = fields.Many2one('account.account', 'Per Diem Account')
    gosi_account_id = fields.Many2one('account.account', 'GOSI Account')
    leave_provision_account_id = fields.Many2one('account.account', 'Leave Provision Account')
    eos_provision_account_id = fields.Many2one('account.account', 'EOS Provision Account')
