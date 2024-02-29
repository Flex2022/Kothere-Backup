# -*- coding: utf-8 -*-

import time
import babel
from odoo import models, fields, api, tools, _
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    loan_line_id = fields.Many2one('hr.loan.line',string="Loan Installment", help="Loan installment")



class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.onchange('struct_id', 'date_from', 'date_to', 'employee_id')
    def onchange_employee_loan(self):
        for data in self:

            if (not data.employee_id) or (not data.date_from) or (not data.date_to):
                return

            lon = data.input_line_ids.filtered(lambda i: i.input_type_id.code == 'LO')
            if lon:
                for loan in lon:
                    loan.unlink()


    def action_payslip_done(self):
        for line in self.input_line_ids:
            if line.loan_line_id:
                line.loan_line_id.paid = True
                line.loan_line_id.loan_id._compute_loan_amount()
        return super(HrPayslip, self).action_payslip_done()


    def _prepare_line_values(self, line, account_id, date, debit, credit):
        if line.salary_rule_id.is_loan:
            partner = line.slip_id.employee_id.related_partner.id
        else:
            partner= line.partner_id.id
        return {
            'name': line.name,
            'partner_id': partner,
            'account_id': account_id,
            'journal_id': line.slip_id.struct_id.journal_id.id,
            'date': date,
            'debit': debit,
            'credit': credit,
            # 'analytic_account_id': line.salary_rule_id.analytic_account_id.id or line.slip_id.contract_id.analytic_account_id.id,
        }

    def input_data_loan_line(self,amount, loan):
            check_lines = []
            new_name = self.env['hr.payslip.input.type'].search([
                ('code', '=', 'LO')])
            for rec in new_name:
                line = (0, 0, {
                    'input_type_id': rec.id,
                    'amount': amount,
                    'name': 'LO',
                    'loan_line_id': loan
                })
            check_lines.append(line)
            return check_lines




    def compute_sheet(self):
        self.onchange_employee_loan()
        self.update_input_list_loan()
        res = super(HrPayslip, self).compute_sheet()
        return res

    def update_input_list_loan(self):
        for rec in self:
            list_loan = rec.get_employee_loan_input_list()
            list = list_loan
            _logger.log(25, 'list' + str(list))
            rec.input_line_ids = list


    def get_employee_loan_input_list(self):
        list = []
        for data in self:
            if (not data.employee_id) or (not data.date_from) or (not data.date_to):
                return
            loan_line = data.struct_id.rule_ids.filtered(
                lambda x: x.code == 'LO')
            if loan_line:
                get_amount = self.env['hr.loan'].search([
                    ('employee_id', '=', data.employee_id.id),
                    ('state', '=', 'paid'),
                    ('payment_id', '!=', [])
                ])
                if get_amount:
                    for lines in get_amount:
                        for line in lines.loan_lines:
                            if data.date_from <= line.date <= data.date_to:
                                if not line.paid:
                                    amount = line.amount
                                    loan = line.id
                                    list = data.input_data_loan_line(amount, loan)
        return list













class HrPayslipInputType(models.Model):
    _inherit = 'hr.payslip.input.type'

    input_id = fields.Many2one('hr.salary.rule')


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    company_id = fields.Many2one('res.company', 'Company', copy=False, readonly=True, help="Comapny",
                                 default=lambda self: self.env.company)
    is_loan = fields.Boolean('Loan')


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    company_id = fields.Many2one('res.company', 'Company', copy=False, readonly=True, help="Comapny",
                                 default=lambda self: self.env.company)
