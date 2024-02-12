# -*- coding: utf-8 -*-

from odoo import fields, models, _, api
from odoo.exceptions import ValidationError
from . import notification_and_email


class SalaryIncrease(models.Model):
    _name = 'salary.increase'
    _description = 'Salary Increase'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Name', copy=False, help="Name", track_visibility='always', states={'draft': [('readonly', False)], 'submit': [('readonly', False)]})
    company_id = fields.Many2one('res.company', 'Company', help="Company",
                                 default=lambda self: self.env.user.company_id,  track_visibility='always',
                                 states={'draft': [('readonly', False)], 'submit': [('readonly', False)]})
    date = fields.Date('Date', default=lambda self: fields.datetime.now(), track_visibility='always',
                       states={'draft': [('readonly', False)], 'submit': [('readonly', False)]})
    user_id = fields.Many2one('res.users', string='Responsable', index=True, tracking=True,
                              default=lambda self: self.env.user, check_company=True,
                              states={'draft': [('readonly', False)], 'submit': [('readonly', False)]})
    type = fields.Selection([('all', 'All Employee'), ('selected', 'Selected Employee')], 'Type',
                            states={'draft': [('readonly', False)], 'submit': [('readonly', False)]})
    increase_percent = fields.Float('Increase Percent (%)',
                                    states={'draft': [('readonly', False)], 'submit': [('readonly', False)]})
    line_ids = fields.One2many('salary.increase.line', 'increase_id', 'Line',
                               states={'draft': [('readonly', False)], 'submit': [('readonly', False)]})
    state = fields.Selection([('draft', 'Draft'), ('submit', 'Submitted'), ('acc_approve', 'Accounting Approved'),
                              ('ceo_approve', 'CEO Approved'), ('hr_approve', 'HR Approved')], string='Status', default='draft')

    def unlink(self):
        line = self.mapped('line_ids')
        if line:
            line.unlink()
        return super(SalaryIncrease, self).unlink()

    @api.onchange('type')
    def onchange_type(self):
        if self.type == 'all':
            lines = []
            employee_ids = self.env['hr.employee'].search([])
            for employee in employee_ids:
                lines.append((0, 0, {'date': fields.Date.today(),
                                     'employee_id': employee.id,
                                     'contract_id': employee.contract_id.id,
                                     'current_salary': employee.contract_id.wage,
                                     'current_variable_increase': employee.contract_id.variable_increase,
                                     'new_salary': employee.contract_id.total_salary + (employee.contract_id.total_salary * self.increase_percent / 100),
                                     'new_variable_increase': 0.0,
                                     'type': 'annual'}))
            self.line_ids = lines

    @api.onchange('increase_percent', 'type')
    def onchange_increase_percent(self):
        if self.line_ids and self.increase_percent:
            for line in self.line_ids:
                line.new_salary = line.current_salary + (line.current_salary * (self.increase_percent / 100))
                salary_increase_amount = line.current_salary * (self.increase_percent / 100)
                line.salary_increase_amount = salary_increase_amount

    def action_submitted(self):
        user_id = self.env['res.users'].search([('groups_id', 'in', self.env.ref('account.group_account_manager').id)], limit=1, order="id desc")
        note = _('<p>Dear %s <br><br> There is a request for a salary increase. Please review it and take the '
                 'necessary action  <br><br> Best Regards,</p>') % (user_id.name)
        warning = _('Please set account manager.')
        date = fields.Date.today()
        activity_type = 'mail.mail_activity_data_todo'
        model = 'salary.increase'
        notification_and_email.notification(self, user_id, date, activity_type, model, note, warning)
        self.state = 'submit'

    def action_accounting_approve(self):
        self.activity_ids.action_feedback(feedback='So much feedback')
        user_id = self.env['res.users'].search([('groups_id', 'in', self.env.ref('hr_employee_updation.group_ceo_approval').id)], limit=1, order="id desc")
        note = _('<p>Dear %s <br><br> There is a request for a salary increase. Please review it and take the '
                 'necessary action  <br><br> Best Regards,</p>') % (user_id.name)
        warning = _('Please set CEO manager.')
        date = fields.Date.today()
        activity_type = 'mail.mail_activity_data_todo'
        model = 'salary.increase'
        notification_and_email.notification(self, user_id, date, activity_type, model, note, warning)
        self.state = 'acc_approve'

    def action_ceo_approve(self):
        self.activity_ids.action_feedback(feedback='So much feedback')
        user_id = self.env['res.users'].search([('groups_id', 'in', self.env.ref('hr.group_hr_manager').id)], limit=1, order="id desc")
        note = _('<p>Dear %s <br><br> There is a request for a salary increase. Please review it and take the '
                 'necessary action  <br><br> Best Regards,</p>') % (user_id.name)
        warning = _('Please set HR manager.')

        date = fields.Date.today()
        activity_type = 'mail.mail_activity_data_todo'
        model = 'salary.increase'
        notification_and_email.notification(self, user_id, date, activity_type, model, note, warning)
        self.state = 'ceo_approve'

    def action_hr_approve(self):
        self.activity_ids.action_feedback(feedback='So much feedback')
        self.increases_distribution()
        self.state = 'hr_approve'

    def increases_distribution(self):
        for line in self.line_ids:
            if line.contract_id:
                if line.type in ('annual', 'exceptional', 'exc_inv'):
                    basic = line.new_salary
                    line.contract_id.wage = basic
                    line.contract_id.housing_allowance_value = basic * 0.25
                    line.contract_id.transportation_allowance_value = basic * 0.10
                    if line.type == 'exc_inv':
                        line.contract_id.variable_increase = line.new_variable_increase
                else:
                    line.contract_id.variable_increase = line.new_variable_increase


class SalaryIncreaseLine(models.Model):
    _name = 'salary.increase.line'
    _description = 'Salary Increase Line'

    increase_id = fields.Many2one('salary.increase', 'Increase')
    date = fields.Date('Date', default=lambda self: fields.datetime.now())
    employee_id = fields.Many2one('hr.employee', 'Employee')
    contract_id = fields.Many2one('hr.contract', 'Contract')
    currency_id = fields.Many2one('res.currency', 'Currency', related='contract_id.currency_id')
    current_salary = fields.Float('Current Salary')
    current_variable_increase = fields.Float('Current Variable Increase')
    new_salary = fields.Float('New Salary')
    new_variable_increase = fields.Float('New Variable Increase')
    type = fields.Selection([('annual', 'Annual Increase'),
                             # ('variable', 'Variable Increase'),
                             # ('exceptional', 'Exceptional Increase'),
                             # ('exc_inv', 'Exceptional & Variable Increase')
                             ], 'type')
    salary_increase_amount = fields.Float('Salary Increase Amount')
    variable_increase_amount = fields.Float('Variable Increase Amount')

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            self.contract_id = self.employee_id.contract_id.id
            self.current_salary = self.employee_id.contract_id.wage
            # self.current_variable_increase = self.employee_id.contract_id.variable_increase

    @api.onchange('type', 'salary_increase_amount', 'variable_increase_amount')
    def onchange_type(self):
        if self.type:
            # if self.type == 'exceptional':
            #     self.new_salary = self.current_salary + self.salary_increase_amount
            #     self.new_variable_increase = self.current_variable_increase
            # elif self.type == 'variable':
            #     self.new_salary = self.current_salary
            #     self.new_variable_increase = self.current_variable_increase + self.variable_increase_amount
            if self.type == 'annual':
                self.new_salary = self.current_salary + self.salary_increase_amount
                # self.new_variable_increase = self.current_variable_increase
            # elif self.type == 'exc_inv':
            #     self.new_salary = self.current_salary + self.salary_increase_amount
            #     self.new_variable_increase = self.current_variable_increase + self.variable_increase_amount


class HrEmployeeContract(models.Model):
    _inherit = 'hr.contract'

    increase_salary_line_ids = fields.One2many('salary.increase.line', 'contract_id', 'Line')
