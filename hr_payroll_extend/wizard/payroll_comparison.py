# -*- coding: utf-8 -*-
from pandas._libs.tslibs.offsets import relativedelta

from odoo import fields, models, api, _


# class RunComparison(models.TransientModel):
#     _name = 'run.comparison'
#     _description = 'Run Comparison'
#
#     number_month = fields.Integer('Number of Month', defaul=1, required=True)


class PayrollComparison(models.Model):
    _name = 'payroll.comparison'
    _description = 'Payroll Comparison'

    name = fields.Char('Name', required=1)
    date = fields.Date('Date', default=fields.Date.today, required=1)
    number_month = fields.Selection([('first', '1'), ('second', '2'), ('third', '3')], string="Number of Month", required=True,
                                    default='first')
    employee_information_first_ids = fields.One2many('employee.payroll.comparison.first', 'payroll_compare',
                                                     string='Employee Information')
    employee_information_second_ids = fields.One2many('employee.payroll.comparison.second', 'payroll_compare',
                                                      string='Employee Information')
    employee_information_third_ids = fields.One2many('employee.payroll.comparison.third', 'payroll_compare',
                                                     string='Employee Information')

    @api.onchange('date')
    def _onchange_comparison(self):
        lines1 = []
        lines2 = []
        lines3 = []
        self.employee_information_first_ids = [(5, 0, 0)]
        self.employee_information_second_ids = [(5, 0, 0)]
        self.employee_information_third_ids = [(5, 0, 0)]
        first_of_month = self.date.replace(day=1)
        first_month = first_of_month-relativedelta(months=1)
        secound_month = first_of_month-relativedelta(months=2)
        third_month = first_of_month-relativedelta(months=3)

        line_in_month = self.env['hr.payslip.run'].search([('date_start', '=', first_of_month)],
                                                          limit=1)
        line_first_month = self.env['hr.payslip.run'].search([('date_start', '=', first_month)],
                                                             limit=1)
        line_second_month = self.env['hr.payslip.run'].search([('date_start', '=', secound_month)],
                                                              limit=1)
        line_third_month = self.env['hr.payslip.run'].search([('date_start', '=', third_month)],
                                                             limit=1)
        if line_in_month:
            for employee in line_in_month.slip_ids:
                exist = 0
                exist2 = 0
                exist3 = 0
                for employee_first in line_first_month.slip_ids:
                    if employee.employee_id.id == employee_first.employee_id.id:
                        exist = 1
                        salary = employee.basic_salary - employee_first.basic_salary
                        transportation = employee.transportation_allowance - employee_first.transportation_allowance
                        housing = employee.housing_allowance - employee_first.housing_allowance
                        other = employee.other_allowance - employee_first.other_allowance
                        gosi = employee.gosi_deduction - employee_first.gosi_deduction
                        loan = employee.loan_deduction - employee_first.loan_deduction
                        net = employee.total_salary - employee_first.total_salary
                        if salary or transportation or housing or other or gosi or loan or net:
                            lines1.append((0, 0, {'employee_id': employee.employee_id.id,
                                                  'basic_salary': salary,
                                                  'transportation': transportation,
                                                  'housing': housing,
                                                  'gosi': gosi,
                                                  'loan': loan,
                                                  'other': other,
                                                  'net': net,
                                                  }))
                for employee_second in line_second_month.slip_ids:
                    if employee.employee_id.id == employee_second.employee_id.id:
                        exist2 = 1
                        salary2 = employee.basic_salary - employee_second.basic_salary
                        transportation2 = employee.transportation_allowance - employee_second.transportation_allowance
                        housing2 = employee.housing_allowance - employee_second.housing_allowance
                        other2 = employee.other_allowance - employee_second.other_allowance
                        gosi2 = employee.gosi_deduction - employee_second.gosi_deduction
                        loan2 = employee.loan_deduction - employee_second.loan_deduction
                        net2 = employee.total_salary - employee_second.total_salary
                        if salary2 or transportation2 or housing2 or other2 or gosi2 or loan2 or net2:
                            lines2.append((0, 0, {'employee_id': employee.employee_id.id,
                                                  'basic_salary': salary2,
                                                  'transportation': transportation2,
                                                  'housing': housing2,
                                                  'gosi': gosi2,
                                                  'loan': loan2,
                                                  'other': other2,
                                                  'net': net2,
                                                  }))
                for employee_third in line_third_month.slip_ids:
                    if employee.employee_id.id == employee_third.employee_id.id:
                        exist3 = 1
                        salary3 = employee.basic_salary - employee_third.basic_salary
                        transportation3 = employee.transportation_allowance - employee_third.transportation_allowance
                        housing3 = employee.housing_allowance - employee_third.housing_allowance
                        other3 = employee.other_allowance - employee_third.other_allowance
                        gosi3 = employee.gosi_deduction - employee_third.gosi_deduction
                        loan3 = employee.loan_deduction - employee_third.loan_deduction
                        net3 = employee.total_salary - employee_third.total_salary
                        if salary3 or transportation3 or housing3 or other3 or gosi3 or loan3 or net3:
                            lines2.append((0, 0, {'employee_id': employee.employee_id.id,
                                                  'basic_salary': salary3,
                                                  'transportation': transportation3,
                                                  'housing': housing3,
                                                  'gosi': gosi3,
                                                  'loan': loan3,
                                                  'other': other3,
                                                  'net': net3,
                                                  }))
                if exist == 0:
                    lines1.append((0, 0, {'employee_id': employee.employee_id.id,
                                          'basic_salary': employee.basic_salary,
                                          'transportation': employee.transportation_allowance,
                                          'housing': employee.other_allowance,
                                          'gosi': employee.gosi_deduction,
                                          'loan': employee.loan_deduction,
                                          'other': employee.other_allowance,
                                          'net': employee.total_salary,
                                          }))
                if exist2 == 0:
                    lines2.append((0, 0, {'employee_id': employee.employee_id.id,
                                          'basic_salary': employee.basic_salary,
                                          'transportation': employee.transportation_allowance,
                                          'housing': employee.other_allowance,
                                          'gosi': employee.gosi_deduction,
                                          'loan': employee.loan_deduction,
                                          'other': employee.other_allowance,
                                          'net': employee.total_salary,
                                          }))
                if exist3 == 0:
                    lines3.append((0, 0, {'employee_id': employee.employee_id.id,
                                          'basic_salary': employee.basic_salary,
                                          'transportation': employee.transportation_allowance,
                                          'housing': employee.other_allowance,
                                          'gosi': employee.gosi_deduction,
                                          'loan': employee.loan_deduction,
                                          'other': employee.other_allowance,
                                          'net': employee.total_salary,
                                          }))

            self.employee_information_first_ids = lines1
            self.employee_information_second_ids = lines2
            self.employee_information_third_ids = lines3


class EmployeePayrollComparisonFirst(models.Model):
    _name = 'employee.payroll.comparison.first'
    _description = 'Employee Payroll Comparison'

    payroll_compare = fields.Many2one('payroll.comparison', 'Payroll Compare')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True,
                                  help='Select the employee who deserves the warning')
    basic_salary = fields.Float('Basic Salary')
    transportation = fields.Float('Transportation')
    housing = fields.Float('Housing')
    # bonus = fields.Float('Bonus')
    # gross = fields.Float('Gross')
    gosi = fields.Float('Gosi')
    loan = fields.Float('Loan')
    other = fields.Float('Other')
    net = fields.Float('Net')


class EmployeePayrollComparisonSecond(models.Model):
    _name = 'employee.payroll.comparison.second'
    _description = 'Employee Payroll Comparison'

    payroll_compare = fields.Many2one('payroll.comparison', 'Payroll Compare')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True,
                                  help='Select the employee who deserves the warning')
    basic_salary = fields.Float('Basic Salary')
    transportation = fields.Float('Transportation')
    housing = fields.Float('Housing')
    # bonus = fields.Float('Bonus')
    # gross = fields.Float('Gross')
    gosi = fields.Float('Gosi')
    loan = fields.Float('Loan')
    other = fields.Float('Other')
    net = fields.Float('Net')


class EmployeePayrollComparisonThird(models.Model):
    _name = 'employee.payroll.comparison.third'
    _description = 'Employee Payroll Comparison'

    payroll_compare = fields.Many2one('payroll.comparison', 'Payroll Compare')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True,
                                  help='Select the employee who deserves the warning')
    basic_salary = fields.Float('Basic Salary')
    transportation = fields.Float('Transportation')
    housing = fields.Float('Housing')
    # bonus = fields.Float('Bonus')
    # gross = fields.Float('Gross')
    gosi = fields.Float('Gosi')
    loan = fields.Float('Loan')
    other = fields.Float('Other')
    net = fields.Float('Net')
