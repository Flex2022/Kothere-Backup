# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from custom.addons.hr_employee_updation.models import notification_and_email


class HREmployeeProvision(models.Model):
    _name = 'hr.employee.provision'
    _description = 'Employee Provision'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    @api.depends('leave_line_ids', 'eos_line_ids')
    def _compute_totals(self):
        for rec in self:
            rec.total_leave = sum(rec.leave_line_ids.mapped('amount'))
            rec.total_eos = sum(rec.eos_line_ids.mapped('amount'))

    name = fields.Char(string='Reference', required=True)
    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)
    office_id = fields.Many2one('hr.employee.office.location', 'Office Location')
    eos_line_ids = fields.One2many('hr.eos.provision.line', 'request_id', 'EOS Line')
    leave_line_ids = fields.One2many('hr.leave.provision.line', 'request_id', 'Leave Line')
    total_leave = fields.Float('Total Leave', compute='_compute_totals', store=True)
    total_eos = fields.Float('Total Provision', compute='_compute_totals', store=True)
    state = fields.Selection([('draft', 'Draft'), ('submit', 'Submitted'), ('done', 'Done')], string='Status', default='draft')

    @api.onchange('office_id')
    def _onchange_office_id(self):
        if self.office_id:
            employee_ids = self.env['hr.employee'].search([('office_id', '=', self.office_id.id), ('employment_type', '=', 'full')])

            leave_list = []
            eos_list = []
            settlement_type_id = self.env['hr.settlement.config'].search([('type', '=', 'Contract Termination'), ('office_id', '=', self.office_id.id)])
            for employee in employee_ids:
                contract = employee.contract_id
                if contract:
                    total_amount = 0.0
                    percentage = 0.0
                    years = contract.service_year
                    months = contract.service_month
                    days = contract.service_day
                    employee_salary = contract.total_salary
                    for line in settlement_type_id.line_ids:
                        if line.percentage > 0.0:
                            if (contract.service_year >= line.from_year and contract.service_year < line.to_year) or contract.service_year >= line.to_year:
                                if contract.service_year == line.to_year:
                                    total_amount += employee_salary * line.salary_per_year * line.to_year
                                    years -= line.to_year
                                elif contract.service_year > line.to_year:
                                    total_amount += employee_salary * line.salary_per_year * line.to_year
                                    years -= line.to_year
                                else:
                                    total_years = employee_salary * line.salary_per_year * years
                                    total_months = employee_salary * line.salary_per_year / 12 * months
                                    total_days = employee_salary * line.salary_per_year / 365 * days
                                    total_amount += total_years + total_months + total_days
                                    percentage = line.percentage

                    total_eos = total_amount * percentage

                    eos_list.append([0, False, {'employee_number': employee.employee_number,
                                                'employee_id': employee.id,
                                                'analytic_distrbution': contract.analytic_distrbution.id,
                                                'department_id': employee.department_id.id,
                                                'contract_id': employee.contract_id.id,
                                                'service_year': contract.service_year,
                                                'service_month': contract.service_month,
                                                'service_day': contract.service_day,
                                                'opening_balance': employee.contract_id.eos_provision,
                                                'total_salary': contract.total_salary,
                                                'name': 'EOS Provision from %s to %s' % (self.start_date, self.end_date),
                                                'total_provision': total_eos}])

                    if employee.remaining_leaves > 0.0:
                        leave_list.append([0, False, {'employee_number': employee.employee_number,
                                                      'employee_id': employee.id,
                                                      'analytic_distrbution': contract.analytic_distrbution.id,
                                                      'contract_id': employee.contract_id.id,
                                                      'department_id': employee.department_id.id,
                                                      'total_salary': contract.total_salary,
                                                      'opening_balance': employee.contract_id.leave_provision,
                                                      'remaining_leaves': employee.remaining_leaves,
                                                      'name': 'Leaves Provision from %s to %s' % (self.start_date, self.end_date),
                                                      'total_provision': "%.2f" % round(contract.total_salary / 30 * employee.remaining_leaves, 2)}])

            self.eos_line_ids = eos_list
            self.leave_line_ids = leave_list

    def action_submit(self):
        self.activity_ids.action_feedback(feedback='So much feedback')
        user_id = self.env['res.users'].search([('groups_id', 'in', self.env.ref('hr_employee_updation.group_chief_accountant').id)], limit=1, order="id desc")
        note = _('<p>Kindly review and approve.</p>')
        warning = _('Please set chief accountant.')
        date = fields.Date.today()
        activity_type = 'mail.mail_activity_data_todo'
        model = 'hr.employee.provision'
        notification_and_email.notification(self, user_id, date, activity_type, model, note, warning)
        self.state = 'submit'

    def action_done(self):
        self.activity_ids.action_feedback(feedback='So much feedback')
        eos_departments = {}
        for record in self.eos_line_ids:
            record.contract_id.write({'eos_provision': record.total_provision})
            key = record.department_id.name or 'general'
            if key not in eos_departments:
                eos_departments[key] = record.amount
            else:
                eos_departments[key] += record.amount

        eos_line_ids = []
        for dep in eos_departments:
            department_id = self.env['hr.department'].search([('name', '=', dep)])
            journal_id = self.env.company.increase_journal_id.id
            eos_credit_account_id = department_id.eos_provision_account_id.id
            eos_debit_account_id = department_id.eos_account_id.id
            name = _('EOS Provision of %s') % self.end_date.strftime('%d/%Y (%B, %Y)')
            accounting_date = self.end_date
            move_dict = {
                'narration': self.name,
                'ref': name,
                'date': accounting_date,
            }
            debit_line = (0, 0, {
                'account_id': eos_debit_account_id,
                'journal_id': journal_id,
                'date': accounting_date,
                'debit': abs(eos_departments[dep] if eos_departments[dep] > 0.0 else 0.0),
                'credit': abs(0.0 if eos_departments[dep] > 0.0 else eos_departments[dep]),
                'analytic_distrbution': department_id.analytic_distrbution.id,
            })
            eos_line_ids.append(debit_line)

            credit_line = (0, 0, {
                'account_id': eos_credit_account_id,
                'journal_id': journal_id,
                'date': accounting_date,
                'debit': abs(0.0 if eos_departments[dep] > 0.0 else eos_departments[dep]),
                'credit': abs(eos_departments[dep] if eos_departments[dep] > 0.0 else 0.0),
                'analytic_distrbution': department_id.analytic_distrbution.id,
            })
            eos_line_ids.append(credit_line)

        if eos_line_ids:
            move_dict['line_ids'] = eos_line_ids
            move_dict['journal_id'] = journal_id
            self.env['account.move'].create(move_dict)

        leave_departments = {}
        for ll in self.leave_line_ids:
            ll.contract_id.write({'leave_provision': ll.total_provision})
            key = ll.department_id.name or 'general'

            if key not in leave_departments:
                leave_departments[key] = ll.amount
            else:
                leave_departments[key] += ll.amount

        leave_line_ids = []
        for leave_dep in leave_departments:
            department_id = self.env['hr.department'].search([('name', '=', leave_dep)])
            journal_id = self.env.company.increase_journal_id.id
            leave_credit_account_id = department_id.leave_provision_account_id.id
            leave_debit_account_id = department_id.leave_account_id.id
            name = _('Leave Provision of %s') % self.end_date.strftime('%d/%Y (%B, %Y)')
            accounting_date = self.end_date
            move_dict = {
                'narration': self.name,
                'ref': name,
                'date': accounting_date,
            }

            leave_debit_line = (0, 0, {
                'account_id': leave_debit_account_id,
                'journal_id': journal_id,
                'date': accounting_date,
                'debit': abs(leave_departments[leave_dep] if leave_departments[leave_dep] > 0.0 else 0.0),
                'credit': abs(0.0 if leave_departments[leave_dep] > 0.0 else leave_departments[leave_dep]),
                'analytic_distrbution': department_id.analytic_distrbution.id,
            })
            leave_line_ids.append(leave_debit_line)

            leave_credit_line = (0, 0, {
                'account_id': leave_credit_account_id,
                'journal_id': journal_id,
                'date': accounting_date,
                'debit': abs(0.0 if leave_departments[leave_dep] > 0.0 else leave_departments[leave_dep]),
                'credit': abs(leave_departments[leave_dep] if leave_departments[leave_dep] > 0.0 else 0.0),
                'analytic_distrbution': department_id.analytic_distrbution.id,
            })
            leave_line_ids.append(leave_credit_line)

        if leave_line_ids:
            move_dict['line_ids'] = leave_line_ids
            move_dict['journal_id'] = journal_id
            self.env['account.move'].create(move_dict)

        self.state = 'done'

    def _generate_quarter_provision(self):
        current_date = fields.Date.today()
        current_quarter = int((current_date.month - 1) / 3 + 1)
        quarter_first_day = datetime(current_date.year, 3 * current_quarter - 2, 1)
        quarter_last_day = datetime(current_date.year, (3 * current_quarter) % 12 + 1, 1) + timedelta(days=-1)
        if fields.Date.today() == quarter_last_day:
            provision = self.env['hr.employee.provision'].create({'name': 'Provision Q' + str(current_quarter),
                                                                  'start_date': quarter_first_day,
                                                                  'end_date': quarter_last_day,
                                                                  'office_id': 1})
            provision._onchange_office_id()


class HREOSProvisionLine(models.Model):
    _name = 'hr.eos.provision.line'
    _description = 'EOS Provision Line'

    @api.depends('total_provision', 'opening_balance')
    def _compute_amount(self):
        for rec in self:
            rec.amount = rec.total_provision - rec.opening_balance

    name = fields.Char(string='Reference')
    request_id = fields.Many2one('hr.employee.provision', 'Request', required=True)
    start_date = fields.Date('Start Date', related='request_id.start_date', store=True)
    end_date = fields.Date('End Date', related='request_id.end_date', store=True)
    employee_number = fields.Char('Employee Number')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    joining_date = fields.Date('Joining Date', related='employee_id.joining_date')
    contract_id = fields.Many2one('hr.contract', 'Contract')
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', store=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    service_year = fields.Integer('Service Years')
    service_month = fields.Integer('Service Months')
    service_day = fields.Integer('Service Days')
    total_salary = fields.Float('Total Salary')
    opening_balance = fields.Float('Opening Balance', store=True)
    total_provision = fields.Float('Total Provision')
    amount = fields.Float('Amount', compute='_compute_amount', store=True)

    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        if self.contract_id:
            self.opening_balance = self.contract_id.eos_provision


class HRLeaveProvisionLine(models.Model):
    _name = 'hr.leave.provision.line'
    _description = 'Leave Provision Line'

    @api.depends('total_provision', 'opening_balance')
    def _compute_amount(self):
        for rec in self:
            rec.amount = rec.total_provision - rec.opening_balance

    name = fields.Char(string='Reference')
    request_id = fields.Many2one('hr.employee.provision', 'Request', required=True)
    start_date = fields.Date('Start Date', related='request_id.start_date', store=True)
    end_date = fields.Date('End Date', related='request_id.end_date', store=True)
    employee_number = fields.Char('Employee Number')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    joining_date = fields.Date('Joining Date', related='employee_id.joining_date')
    contract_id = fields.Many2one('hr.contract', 'Contract')
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', store=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    remaining_leaves = fields.Float('Remaining Leaves')
    opening_balance = fields.Float('Opening Balance', store=True)
    total_salary = fields.Float('Total Salary')
    total_provision = fields.Float('Total Provision')
    amount = fields.Float('Amount', compute='_compute_amount', store=True)

    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        if self.contract_id:
            self.opening_balance = self.contract_id.leave_provision
