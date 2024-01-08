# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

import calendar
from odoo import fields, models, _, api
from odoo.exceptions import ValidationError


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    number_of_days = fields.Integer('Number of Days', compute='_check_date')
    last_day_month = fields.Integer('Last Day of Month', compute='_compute_last_day_month')

    def notification(self, user_id, date, activity_type, model, note, warning):
        if user_id:
            notification = {
                'activity_type_id': self.env.ref(activity_type).id,
                'res_id': self.id,
                'res_model_id': self.env['ir.model'].search([('model', '=', model)], limit=1).id,
                'icon': 'fa-pencil-square-o',
                'date_deadline': date,
                'user_id': user_id.id,
                'note': note
            }
            self.env['mail.activity'].create(notification)
        else:
            raise ValidationError(warning)

    def send_email(self, email_to, auther, subject, mail_content, warning):
        if email_to:
            main_content = {
                'subject': subject,
                'author_id': auther,
                'body_html': mail_content,
                'email_to': email_to,
            }
            self.env['mail.mail'].sudo().create(main_content).send()
        else:
            raise ValidationError(warning)

    @api.constrains('date_from', 'date_to')
    def _check_date(self):
        for rec in self:
            if rec.date_from > rec.date_to:
                raise ValidationError(_("The start date must be before the end date."))
            rec._compute_number_of_days()

    @api.depends('date_from', 'date_to')
    def _compute_number_of_days(self):
        for rec in self:
            if rec.date_from and rec.date_to:
                rec.number_of_days = (rec.date_to - rec.date_from).days + 1

    @api.depends('date_from')
    def _compute_last_day_month(self):
        for rec in self:
            if rec.date_from:
                rec.last_day_month = calendar.monthrange(rec.date_from.year, rec.date_from.month)[1]

    @api.depends('line_ids', 'state')
    def _compute_salary_amount(self):
        for rec in self:
            BASIC = rec.line_ids.filtered(lambda x: x.category_id.code == 'BASIC')
            rec.basic_salary = BASIC.total

            HOUSING = rec.line_ids.filtered(lambda y: y.name == 'Housing')
            rec.housing_allowance = HOUSING.total

            TRANS = rec.line_ids.filtered(lambda z: z.name == 'Transportation')
            rec.transportation_allowance = TRANS.total

            OTHER = rec.line_ids.filtered(lambda m: m.name == 'Bonus')
            rec.other_allowance = OTHER.total

            GROSS = rec.line_ids.filtered(lambda w: w.category_id.code == 'GROSS')
            rec.gross_salary = GROSS.total

            LOAN = rec.line_ids.filtered(lambda n: n.name == 'Loan')
            rec.loan_deduction = LOAN.total

            OTHER_DED = rec.line_ids.filtered(lambda n: n.name == 'Other Deduction')
            rec.other_deduction = OTHER_DED.total

            GOSI = rec.line_ids.filtered(lambda o: o.name == 'GOSI')
            rec.gosi_deduction = GOSI.total

            NET = rec.line_ids.filtered(lambda x: x.code == 'NET')
            rec.total_salary = NET.total

    basic_salary = fields.Float('Basic Salary', store=True, compute='_compute_salary_amount')
    housing_allowance = fields.Float('Housing', store=True, compute='_compute_salary_amount')
    transportation_allowance = fields.Float('Transportation', store=True, compute='_compute_salary_amount')
    other_allowance = fields.Float('Other', store=True, compute='_compute_salary_amount')
    gross_salary = fields.Float('Gross', store=True, compute='_compute_salary_amount')
    gosi_deduction = fields.Float('GOSI', store=True, compute='_compute_salary_amount')
    loan_deduction = fields.Float('Loan', store=True, compute='_compute_salary_amount')
    other_deduction = fields.Float('Other Deduction', store=True, compute='_compute_salary_amount')
    total_salary = fields.Float('Net Salary', store=True, compute='_compute_salary_amount')
    department_id = fields.Many2one('hr.department', string='Department', store=True,
                                    related='employee_id.department_id',
                                    domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    joining_date = fields.Date('Joining Date', related='employee_id.joining_date')

    @api.constrains('employee_id')
    def validate_employee_id(self):
        for rec in self:
            payslip_ids = self.env['hr.payslip'].search(
                [('employee_id', '=', rec.employee_id.id), ('date_from', '=', rec.date_from),
                 ('date_to', '=', rec.date_to)])
            if len(payslip_ids) > 1:
                raise ValidationError(
                    _('You cant create more than one payslip for the employee (%s) in the same month' % rec.employee_id.name))


class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    payslip_run_id = fields.Many2one('hr.payslip.run', string='Payslip Batches', store=True,
                                     related='slip_id.payslip_run_id')
    department_id = fields.Many2one('hr.department', string='Department', store=True,
                                    related='employee_id.department_id',
                                    domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', store=True)

    @api.onchange('contract_id')
    def onchange_analytic_account(self):
        self.analytic_account_id = self.contract_id.analytic_distrbution.id

    @api.model
    def create(self, vals):
        if 'contract_id' in vals:
            contract_id = self.env['hr.contract'].browse(vals['contract_id'])
            vals['analytic_distrbution'] = contract_id.analytic_distrbution.id
        res = super(HrPayslipLine, self).create(vals)
        return res


class HrEmployeeContract(models.Model):
    _inherit = 'hr.contract'

    account_id = fields.Many2one('account.account', 'Employee Account')


class HrPayslipRun(models.Model):
    _name = 'hr.payslip.run'
    _inherit = ['hr.payslip.run', 'mail.thread', 'mail.activity.mixin']

    number_of_days = fields.Integer('Number of Days', compute='_check_date')
    last_day_month = fields.Integer('Last Day of Month', compute='_compute_last_day_month')

    # add validation on date_end to be greater than or equal date_start then compute _compute_number_of_days
    @api.constrains('date_start', 'date_end')
    def _check_date(self):
        for rec in self:
            if rec.date_start > rec.date_end:
                raise ValidationError(_("The start date must be before the end date."))
            rec._compute_number_of_days()

    @api.depends('date_start', 'date_end')
    def _compute_number_of_days(self):
        for rec in self:
            if rec.date_start and rec.date_end:
                rec.number_of_days = (rec.date_end - rec.date_start).days + 1

    @api.depends('date_start')
    def _compute_last_day_month(self):
        for rec in self:
            if rec.date_start:
                rec.last_day_month = calendar.monthrange(rec.date_start.year, rec.date_start.month)[1]

    @api.depends('slip_ids', 'slip_ids.total_salary')
    def _compute_totals(self):
        for rec in self:
            total = 0.0
            for line in rec.slip_ids:
                total += line.total_salary
            rec.total = total

    payment_id = fields.Many2one('account.payment', string="Payment", copy=False,
                                 help="Payment that created this entry")
    adjust_request = fields.Text(string="Adjust Request")
    total = fields.Float('Total', compute='_compute_totals', store=True)
    state = fields.Selection(selection_add=[('draft', 'Draft'), ('hr', 'HR Preparation'), ('accounting', 'Accounting Preparation'),
                              ('ceo_approve', 'CEO Approve'),
                              ('done', 'Done'), ('close', 'Close'), ], string='Status',
                             index=True, readonly=True, copy=False, default='draft')

    def action_sent_to_accounting(self):
        user_id = self.env['res.users'].search([('groups_id', 'in', self.env.ref('account.group_account_manager').id)],
                                               limit=1, order="id desc")
        note = _('<p>Kindly review and approve.</p>')
        warning = _('Please set account manager.')
        date = fields.Date.today()
        activity_type = 'mail.mail_activity_data_todo'
        model = 'hr.payslip.run'
        self.notification(self, user_id, date, activity_type, model, note, warning)
        self.state = 'accounting'

    def action_sent_to_ceo(self):
        self.activity_ids.action_feedback(feedback='So much feedback')
        user_id = self.env['res.users'].search(
            [('groups_id', 'in', self.env.ref('hr_employee_updation.group_ceo_approval').id)], limit=1, order="id desc")
        note = _('<p>Kindly review and approve.</p>')
        warning = _('Please set CEO manager.')
        date = fields.Date.today()
        activity_type = 'mail.mail_activity_data_todo'
        model = 'hr.payslip.run'
        self.notification(self, user_id, date, activity_type, model, note, warning)
        self.state = 'ceo_approve'

    def action_sent_to_hr(self):
        self.activity_ids.action_feedback(feedback='So much feedback')
        hr_user_id = self.env['res.users'].search([('groups_id', 'in', self.env.ref('hr.group_hr_manager').id)],
                                                  limit=1, order="id desc")
        note = _('<p>Kindly review and approve.')
        warning = _('Please set HR manager.')
        date = fields.Date.today()
        activity_type = 'mail.mail_activity_data_todo'
        model = 'hr.payslip.run'
        self.notification(self, hr_user_id, date, activity_type, model, note, warning)
        self.state = 'hr'

    def calculate_loan_deduction(self, slip):
        for line in slip.input_line_ids:
            if line.loan_line_id:
                amount = line.amount
                if amount > 0.0:
                    if line.loan_line_id.paid_amount == 0.0:
                        if amount == line.loan_line_id.amount:
                            line.loan_line_id.paid = True
                            line.loan_line_id.paid_amount = amount
                            amount = 0.0
                        elif amount < line.loan_line_id.amount:
                            line.loan_line_id.paid_amount = amount
                            amount = 0.0
                        elif amount > line.loan_line_id.amount:
                            line.loan_line_id.paid = True
                            line.loan_line_id.paid_amount = line.loan_line_id.amount
                            amount -= line.loan_line_id.amount
                            loan_line_ids = self.env['hr.loan.line'].search(
                                [('loan_id', '=', line.loan_line_id.loan_id.id), ('paid', '=', False)])
                            for rec in loan_line_ids:
                                if amount >= rec.amount:
                                    rec.paid_amount = rec.amount
                                    rec.paid = True
                                    amount -= rec.amount
                                elif amount < rec.amount and amount != 0.0:
                                    rec.paid_amount = amount
                                    amount = 0.0
                    else:
                        remaining_amount = line.loan_line_id.amount - line.loan_line_id.paid_amount
                        if amount == remaining_amount:
                            line.loan_line_id.paid = True
                            line.loan_line_id.paid_amount = amount
                        elif amount < remaining_amount:
                            line.loan_line_id.paid_amount += amount
                        elif amount > remaining_amount:
                            line.loan_line_id.paid = True
                            line.loan_line_id.paid_amount = line.loan_line_id.amount

                            amount -= remaining_amount
                            loan_line_ids = self.env['hr.loan.line'].search(
                                [('loan_id', '=', line.loan_line_id.loan_id.id), ('paid', '=', False)])
                            for rec in loan_line_ids:
                                if amount >= rec.amount:
                                    rec.paid_amount = rec.amount
                                    rec.paid = True
                                    amount -= rec.amount
                                elif amount < rec.amount and amount != 0.0:
                                    rec.paid_amount += amount
                                    amount = 0.0

    def action_done(self):
        self.activity_ids.action_feedback(feedback='So much feedback')
        analytic_accounts = {}
        for record in self.slip_ids:
            if record.state == 'draft':
                key = record.employee_id.contract_id.analytic_distrbution.name or record.employee_id.department_id.analytic_distrbution.name or 'general'

                if key not in analytic_accounts:
                    analytic_accounts[key] = [record]
                else:
                    analytic_accounts[key].append(record)

        for acc in analytic_accounts:
            debit = {}
            credit = {}
            line_ids = []
            name = _('Payslip of %s') % acc
            currency = self.env.company.currency_id
            move_dict = {
                'narration': self.name,
                'ref': name,
            }
            debit[acc] = {}
            credit[acc] = {}
            for slip in analytic_accounts[acc]:
                date = slip.date_to
                journal_id = slip.journal_id.id
                self.calculate_loan_deduction(slip)
                for line in slip.details_by_salary_rule_category:
                    X = line.name
                    if line.salary_rule_id.account_credit.id or line.salary_rule_id.account_debit.id:
                        key1 = line.salary_rule_id.account_debit.id or line.contract_id.account_id.id
                        if key1 not in debit[acc]:
                            debit[acc][key1] = currency.round(slip.credit_note and -line.total or line.total)
                        else:
                            debit[acc][key1] += currency.round(slip.credit_note and -line.total or line.total)

                        key2 = line.salary_rule_id.account_credit.id or line.contract_id.account_id.id
                        if key2 not in credit[acc]:
                            credit[acc][key2] = currency.round(slip.credit_note and -line.total or line.total)
                        else:
                            credit[acc][key2] += currency.round(slip.credit_note and -line.total or line.total)

                slip.state = 'done'

            for group_line in debit:
                for line in debit[group_line]:
                    if debit[group_line][line] != 0.0:
                        debit_line = (0, 0, {
                            'account_id': line,
                            'journal_id': journal_id,
                            'date': date,
                            'debit': abs(debit[group_line][line]),
                            'credit': 0.0,
                            'name': name,
                            'analytic_distrbution': self.env['account.analytic.account'].search(
                                [('name', '=', group_line)], limit=1).id,
                        })
                        line_ids.append(debit_line)

            for group_cline in credit:
                for cline in credit[group_cline]:
                    if credit[group_cline][cline] != 0.0:
                        credit_line = (0, 0, {
                            'account_id': cline,
                            'journal_id': journal_id,
                            'date': date,
                            'debit': 0.0,
                            'name': name,
                            'credit': abs(credit[group_cline][cline]),
                            'analytic_distrbution': self.env['account.analytic.account'].search(
                                [('name', '=', group_line)], limit=1).id,
                        })
                        line_ids.append(credit_line)

            if line_ids:
                move_dict['line_ids'] = line_ids
                move_dict['journal_id'] = journal_id
                move_dict['date'] = date
                self.env['account.move'].create(move_dict)
        self.state = 'done'
        self.create_payment_action()
        user_id = self.env['res.users'].search([('groups_id', 'in', self.env.ref('hr.group_hr_manager').id)], limit=1,
                                               order="id desc")
        mail_content = "Hello  " + user_id.name + ",<br> <br> We would like to inform you that request " + self.name + ". He was sent to the financial department to take necessary action. <br><br> Best Regards,"
        author = user_id.partner_id.id
        subject = _('Approved Request')
        email_to = user_id.email
        warning = ""
        self.send_email(self, email_to, author, subject, mail_content, warning)

    def _upload_payslip_batch_reminder(self):
        batch_ids = self.env['hr.payslip.run'].search([])
        for rec in batch_ids:
            current_year = fields.Date.today()
            write_date = rec.write_date.date()
            if write_date:
                hr_user_id = self.env['res.users'].search([('groups_id', 'in', self.env.ref('hr.group_hr_manager').id)],
                                                          limit=1, order="id desc")
                accounting_user_id = self.env['res.users'].search(
                    [('groups_id', 'in', self.env.ref('account.group_account_manager').id)], limit=1, order="id desc")
                diff_date = (current_year - write_date).days
                if diff_date == 5 and rec.state == 'done':
                    mail_content = "Dears," + "<br> <br> We would like to remind you to upload salary sheet" + "<br><br> Best Regards,"
                    author = accounting_user_id.partner_id.id
                    subject = _('Upload Salary Sheet')
                    email_to = hr_user_id.email + ',' + accounting_user_id.email
                    warning = ""
                    self.send_email(rec, email_to, author, subject, mail_content, warning)

    def create_payment_action(self):
        journal = self.env['account.journal'].search([('type', 'in', ('bank', 'cash'))], limit=1)

        payment_methods = (self.total > 0) and journal.inbound_payment_method_line_ids or journal.outbound_payment_method_line_ids
        payment_list = [{
            'payment_method_id': payment_methods and payment_methods[0].id or False,
            'payment_type': 'outbound',
            'partner_id': self.env.company.id,
            'payroll_batch_id': self.id,
            'partner_type': 'employee',
            'journal_id': journal.id,
            'payment_date': fields.Date.today(),
            'currency_id': self.env.company.currency_id.id,
            'amount': self.total,
            'communication': self.name,
        }]
        self.payment_id = self.env['account.payment'].sudo().create(payment_list)
        amount_in_word = self.payment_id.currency_id.amount_to_text(
            self.payment_id.amount) if self.payment_id.currency_id else '',
        self.payment_id.check_amount_in_words = amount_in_word[0]

        accountant_id = self.env['res.users'].search(
            [('groups_id', 'in', self.env.ref('hr_employee_updation.group_accountant').id)], limit=1, order="id desc")
        if accountant_id:
            note = _('<p>%s has submitted a <span style="font-weight: bold;">Payroll Request: %s </span> and '
                     'a payment request has been created on it, please view it</p>') \
                   % (self.env.user.name, self.name)
            user_id = accountant_id
            warning = ""
            date = fields.Date.today()
            activity_type = 'hr_extend.hr_request_notification'
            model = 'account.payment'
            self.notification(self.payment_id, user_id, date, activity_type, model, note, warning)


class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'

    """To add security"""


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    """To add security"""
