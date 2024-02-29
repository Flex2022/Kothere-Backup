from odoo import models, fields, api, _
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError


class HrLoan(models.Model):
    _name = 'hr.loan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Loan Request"

    @api.model
    def default_get(self, field_list):
        result = super(HrLoan, self).default_get(field_list)
        if result.get('user_id'):
            ts_user_id = result['user_id']
        else:
            ts_user_id = self.env.context.get('user_id', self.env.user.id)
        result['employee_id'] = self.env['hr.employee'].search([('user_id', '=', ts_user_id)], limit=1).id
        return result

    def _compute_loan_amount(self):
        """to compute balance_amount,total_amount,total_paid_amount after any payment"""
        total_paid = 0.0
        for loan in self:
            for line in loan.loan_lines:
                if line.paid:
                    total_paid += line.amount
            balance_amount = loan.loan_amount - total_paid
            loan.total_amount = loan.loan_amount
            loan.balance_amount = balance_amount
            loan.total_paid_amount = total_paid

    name = fields.Char(string="Loan Name", default="/", readonly=True, help="Name of the loan")
    date = fields.Date(string="Date", default=fields.Date.today(), readonly=True, help="Date")
    user_id = fields.Many2one('res.users', string="User", readonly=True, default=lambda self: self.env.user, help="User")
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, help="Employee")
    department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True,
                                    string="Department", help="Employee")
    installment = fields.Integer(string="No Of Installments", default=1, help="Number of installments")
    payment_date = fields.Date(string="Payment Start Date", required=True, default=fields.Date.today(), help="Date of "
                                                                                                             "the "
                                                                                                             "payment")
    loan_lines = fields.One2many('hr.loan.line', 'loan_id', string="Loan Line", index=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True, help="Company",
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id', help="Currency")
    job_position = fields.Many2one('hr.job', related="employee_id.job_id", readonly=True, string="Job Position",
                                   help="Job position")
    loan_amount = fields.Float(string="Loan Amount", required=True, help="Loan amount")
    total_amount = fields.Float(string="Total Amount", store=True, readonly=True, compute='_compute_loan_amount',
                                help="Total loan amount")
    balance_amount = fields.Float(string="Balance Amount", store=True, compute='_compute_loan_amount',
                                  help="Balance amount")
    total_paid_amount = fields.Float(string="Total Paid Amount", store=True, compute='_compute_loan_amount',
                                     help="Total paid amount")
    payment_id = fields.Many2one('account.payment', string='Payment', )
    payment = fields.Boolean(string='Payment', required=False)
    reason = fields.Char(string="Reason")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval_1', 'Submitted'),
        ('approve', 'Approved'),
        ('refuse', 'Refused'),
        ('paid', 'Paid'),
        ('cancel', 'Canceled'),
    ], string="State", default='draft', tracking=True, copy=False, )

    @api.model_create_multi
    def create(self, values):
        res = super(HrLoan, self).create(values)
        loan_count = self.env['hr.loan'].search_count(
            [('employee_id', '=', res.employee_id.id), ('state', 'in', ('approve', 'paid')),
             ('balance_amount', '!=', 0)])
        if loan_count:
            raise ValidationError(_("The employee has already a pending installment"))

        loan_date = self.env['hr.loan'].search([
            ('employee_id', '=', res.employee_id.id), ('state', 'in', ('approve', 'paid'))])
        current_year = date.today().year
        for lo in loan_date:
            if lo.date.year == current_year:
                raise ValidationError(_("The employee has already a installment in the same year"))
        res.name = self.env['ir.sequence'].get('hr.loan.seq') or ' '

        return res

    def compute_installment(self):
        """This automatically create the installment the employee need to pay to
        company based on payment start date and the no of installments.
            """
        for loan in self:
            loan.loan_lines.unlink()
            date_start = datetime.strptime(str(loan.payment_date), '%Y-%m-%d')
            amount = loan.loan_amount / loan.installment
            for i in range(1, loan.installment + 1):
                self.env['hr.loan.line'].create({
                    'date': date_start,
                    'amount': amount,
                    'employee_id': loan.employee_id.id,
                    'loan_id': loan.id})
                date_start = date_start + relativedelta(months=1)
            loan._compute_loan_amount()
        return True

    def action_refuse(self):
        return self.write({'state': 'refuse'})

    def action_submit(self):
        self.write({'state': 'waiting_approval_1'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_approve(self):
        for data in self:
            if not data.loan_lines:
                raise ValidationError(_("Please Compute installment"))
            if not data.employee_id.related_partner:
                raise ValidationError(_("Please link partner for employee"))
            else:
                self.write({'state': 'approve'})
            #     debit_value = {
            #         'name': self.name,
            #         'debit': self.loan_amount,
            #         'credit': 0.0,
            #         'partner_id': self.employee_id.related_partner.id,
            #         'account_id': self.env.company.debit_account_id.id,
            #     }
            #
            #     credit_value = {
            #         'name': self.name,
            #         'debit': 0.0,
            #         'credit': self.loan_amount,
            #         'partner_id': self.employee_id.related_partner.id,
            #         'account_id': self.env.company.credit_account_id.id,
            #     }
            #
            #     values = {
            #         'journal_id': self.env.company.loan_journal_id.id,
            #         'date': self.date.today(),
            #         'ref': self.name,
            #         'state': 'draft',
            #         'line_ids': [(0, 0, debit_value), (0, 0, credit_value)]}
            #     move = self.env['account.move'].create(values)
            # return move

    def unlink(self):
        for loan in self:
            if loan.state not in ('draft', 'cancel'):
                raise UserError(
                    'You cannot delete a loan which is not in draft or cancelled state')
        return super(HrLoan, self).unlink()

    def action_register_payment(self):
        return {
            'name': "Register Payment",
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'account.payment.loan',
            'view_id': self.env.ref('nthub_loan_management.view_account_payment_loan_form').id,
            'context': {
                'default_partner_id': self.employee_id.related_partner.id,
                'default_amount': self.loan_amount,
                'default_loan_id': self.id,
                'default_communication': f"loan for {self.employee_id.related_partner.name} with {self.loan_amount} with ref {self.name}",
                'active_model': 'hr.loan',
                'active_ids': self.filtered(lambda p: p.balance_amount > 0).ids,
            },
            'target': 'new'
        }

    def loan_Settlement(self):
        """ to settlement all loan balance amount.
            you should to select payment method on journal."""
        if self.balance_amount != 0:
            payment_values = {
                'date': fields.Date.today(),
                'amount': self.balance_amount,
                'payment_type': 'inbound',
                'ref': f"Settlement for {self.employee_id.related_partner.name} with {self.balance_amount} with ref {self.name}",
                # 'journal_id': self.env.company.loan_journal_id.id,
                'currency_id': self.currency_id.id,
                'partner_id': self.employee_id.related_partner.id,
                'payment_loan': True,
                'loan_id': self.id,

            }
            payment = self.env['account.payment'].create(payment_values)
            self.update({'total_paid_amount': self.total_amount})
            self.update({'balance_amount': (self.total_amount - self.total_paid_amount)})
            for rec in self.loan_lines:
                rec.update({'paid': True})

            return payment

    def write(self, vals):
        ret = super(HrLoan, self).write(vals)
        for rec in self:
            if rec.state in ('approve', 'paid'):
                if sum(rec.loan_lines.mapped('amount')) != rec.loan_amount:
                    print(sum(rec.loan_lines.mapped('amount')), 'ddddddddd')
                    raise ValidationError(_("amount in total months must be = loan amount"))

        return ret


class InstallmentLine(models.Model):
    _name = "hr.loan.line"
    _description = "Installment Line"
    _rec_name = "loan_id"

    date = fields.Date(string="Payment Date", required=True, help="Date of the payment")
    employee_id = fields.Many2one('hr.employee', string="Employee", help="Employee")
    amount = fields.Float(string="Amount", required=True, help="Amount")
    paid = fields.Boolean(string="Paid", help="Paid")
    loan_id = fields.Many2one('hr.loan', string="Loan Ref.", help="Loan")
    payslip_id = fields.Many2one('hr.payslip', string="Payslip Ref.", help="Payslip")


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    related_partner = fields.Many2one('res.partner')
    loan_count = fields.Integer(string="Loan Count", compute='_compute_employee_loans')


    @api.constrains('related_partner')
    def check_identification_id(self):
        related_partner_exist = self.env['hr.employee'].search([('related_partner', '=', self.related_partner.id),('id', '!=', self.id)])
        if related_partner_exist:
            raise ValidationError("Related Partner is exist")

    def _compute_employee_loans(self):
        """This compute the loan amount and total loans count of an employee.
            """
        self.loan_count = self.env['hr.loan'].search_count(
            [('employee_id', '=', self.id), ('state', 'in', ('approve','paid'))])

