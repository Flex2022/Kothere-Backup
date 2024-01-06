# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
from . import notification_and_email
import logging

_logger = logging.getLogger(__name__)



class AccountPayment(models.Model):
    _inherit = 'account.payment'
    partner_type = fields.Selection(
        [('customer', 'Customer'), ('supplier', 'Vendor'), ('employee', 'Employee'), ('other', 'Other')],
        tracking=True, readonly=False, states={'draft': [('readonly', False)]})
    vi_id = fields.Many2one('hr.variable.increase', 'Variable Increase')

    def _get_aml_default_display_map(self):
        return {
            ('outbound', 'customer'): _("Customer Reimbursement"),
            ('inbound', 'customer'): _("Customer Payment"),
            ('outbound', 'supplier'): _("Vendor Payment"),
            ('inbound', 'supplier'): _("Vendor Reimbursement"),
            ('outbound', 'employee'): _("Employee Payment"),
            ('inbound', 'employee'): _("Employee Reimbursement"),
            ('outbound', 'other'): _("Other Payment"),
            ('inbound', 'other'): _("Other Reimbursement"),
        }

class HRVariableIncrease(models.Model):
    _name = 'hr.variable.increase'
    _description = 'Variable Increase'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    @api.depends('line_ids', 'line_ids.net_amount')
    def _compute_totals(self):
        for rec in self:
            total = 0.0
            for line in rec.line_ids:
                total += line.net_amount
            rec.total = total

    name = fields.Char(string='Reference', required=True)
    increase_schedule = fields.Selection([('1', 'Monthly'), ('3', 'Quarterly'), ('6', 'Half Yearly')],
                                         string='Increase Schedule', default='3')
    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)
    payment_date = fields.Date('Payment Date')
    office_id = fields.Many2one('hr.employee.office.location', 'Office Location')
    adjust_request = fields.Text(string="Adjust Details")
    payment_id = fields.Many2one('account.payment', string="Payment", copy=False, help="Payment that created this entry")
    line_ids = fields.One2many('hr.variable.increase.line', 'request_id', 'Line')
    total = fields.Float('Total', compute='_compute_totals', store=True)
    state = fields.Selection([('draft', 'Draft'), ('accounting', 'Accounting Preparation'), ('ceo_approve', 'CEO Approve'),
                              ('hr', 'HR Preparation'), ('done', 'Done')], string='Status', default='draft')

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

    @api.onchange('increase_schedule')
    def _onchange_increase_schedule(self):
        if self.increase_schedule:
            current_date = datetime.now()
            current_quarter = (current_date.month - 1) // 3 + 1
            if current_quarter < 13:

                self.start_date = datetime(current_date.year, 3 * int(current_quarter) - 2, 1)
                self.end_date = datetime(current_date.year, 3 * int(current_quarter) - 2, 1) + timedelta(days=-1)

            else:
                print('hello')

    @api.onchange('office_id')
    def _onchange_office_id(self):
        if self.office_id:
            contract_list = []
            contract_ids = self.env['hr.contract'].search([('variable_increase', '>', 0.0), ('increase_schedule', '=', self.increase_schedule), ('employee_id.notice_period_flag', '=', False)])
            for contract in contract_ids:
                if contract.increase_start_date:
                    if contract.increase_start_date <= self.start_date:
                        amount = contract.variable_increase
                    elif contract.increase_start_date > self.start_date and contract.increase_start_date < self.end_date:
                        diff_days = (self.end_date - contract.increase_start_date).days
                        amount = contract.variable_increase / 30 * diff_days
                    elif contract.increase_start_date >= self.end_date:
                        amount = 0.00

                    contract_list.append([0, False, {'employee_id': contract.employee_id.id,
                                                     'name': 'Variable Increase from %s to %s' % (self.start_date, self.end_date),
                                                     'increase_per_month': amount}])
                else:
                    raise ValidationError(_('Please set increase start date for (%s)' % contract.name))

            self.line_ids = contract_list

    def action_sent_to_accounting(self):
        user_id = self.env['res.users'].search([('groups_id', 'in', self.env.ref('account.group_account_manager').id)],limit=1, order="id desc")
        note = _('<p>Kindly review and approve.</p>')
        warning = _('Please set account manager.')
        date = fields.Date.today()
        activity_type = 'mail.mail_activity_data_todo'
        model = 'hr.variable.increase'
        notification_and_email.notification(self, user_id, date, activity_type, model, note, warning)
        self.state = 'accounting'

    def action_sent_to_ceo(self):
        user_id = self.env['res.users'].search(
            [('groups_id', 'in', self.env.ref('hr_employee_updation.group_ceo_approval').id)], limit=1, order="id desc")
        note = _('<p>Kindly review and approve.</p>')
        warning = _('Please set CEO manager.')
        date = fields.Date.today()
        activity_type = 'mail.mail_activity_data_todo'
        model = 'hr.variable.increase'
        notification_and_email.notification(self, user_id, date, activity_type, model, note, warning)
        self.state = 'ceo_approve'

    def action_sent_to_hr(self):
        hr_user_id = self.env['res.users'].search([('groups_id', 'in', self.env.ref('hr.group_hr_manager').id)],
                                                  limit=1, order="id desc")
        note = _('<p>Kindly review and approve.</p>')
        warning = _('Please set HR manager.')
        date = fields.Date.today()
        activity_type = 'mail.mail_activity_data_todo'
        model = 'hr.variable.increase'
        notification_and_email.notification(self, hr_user_id, date, activity_type, model, note, warning)
        self.state = 'hr'

    def action_done(self):
        # Use defaultdict to simplify the department grouping logic
        departments = defaultdict(list)

        for record in self.line_ids:
            key = record.employee_id.department_id.name or 'general'
            departments[key].append(record)

            # Validate increase_per_month at the beginning to prevent further processing
            if record.increase_per_month == 0.0:
                raise ValidationError(_('Increase per month must be greater than zero.'))

        for dep, inc_lines in departments.items():
            department = self.env['hr.department'].search([('name', '=', dep)], limit=1)
            journal_id = self.env.company.increase_journal_id.id
            credit_account_id = self.env.company.increase_account_id.id
            currency_data = self.env.company.currency_id
            debit_account_id = self.env.company.increase_account_id.id
            if department :
                if department.increase_account_id:
                    debit_account_id = department.increase_account_id.id
            total_amount = sum(inc_line.net_amount for inc_line in inc_lines)
            if total_amount > 0.0:
                # Simplify move creation using dictionaries
                move_dict = {
                    'narration': self.name,
                    'ref': _('Variable Increase of %s') % dep,
                    'date': self.end_date,
                    'journal_id': journal_id,
                    'line_ids': [
                        (0, 0, {
                            'account_id': debit_account_id,
                            'currency_id': currency_data.id,
                            'name': _('Variable Increase of %s') % dep,
                            'debit': total_amount,
                            'credit': 0.0,
                            'date': self.end_date,
                            'amount_currency': 0.0,
                        }),
                        (0, 0, {
                            'account_id': credit_account_id,
                            'currency_id': currency_data.id,
                            'name': _('Variable Increase of %s') % dep,
                            'debit': 0.0,
                            'credit': total_amount,
                            'date': self.end_date,
                            'amount_currency': 0.0,
                        }),
                    ],
                }

                # Create move directly with create method
                self.env['account.move'].create(move_dict)

        self.state = 'done'
        self.create_payment_action()

        # Use try-except to handle errors during mail sending
        try:
            user_id = self.env['res.users'].search([('groups_id', 'in', self.env.ref('hr.group_hr_manager').id)],
                                                   limit=1, order="id desc")
            mail_content = f"Hello {user_id.name},<br> <br> We would like to inform you that request {self.name}. It was sent to the financial department for necessary action. <br><br> Best Regards,"
            author = user_id.partner_id.id
            subject = _('Approved Request')
            email_to = user_id.email
            warning = ""
            self.send_email(email_to, author, subject, mail_content, warning)
        except Exception as e:
            _logger.error(f"Error sending email: {e}")

    def create_payment_action(self):
        journal = self.env['account.journal'].search([('type', 'in', ('bank', 'cash'))], limit=1)

        payment_methods = (self.total > 0) and journal.inbound_payment_method_line_ids or journal.outbound_payment_method_line_ids
        payment_list = [{
            'journal_id': journal.id,
            'payment_method_id': payment_methods and payment_methods[0].payment_method_id.id or False,
            'payment_type': 'outbound',
            'partner_id': self.env.company.id,
            'vi_id': self.id,
            'partner_type': 'supplier',
            'date': fields.Date.today(),
            'currency_id': self.env.company.currency_id.id,
            'amount': self.total,
            'ref': self.name,
        }]
        self.payment_id = self.env['account.payment'].sudo().create(payment_list)
        amount_in_word = self.payment_id.currency_id.amount_to_text(self.payment_id.amount) if self.payment_id.currency_id else '',
        self.payment_id.check_amount_in_words = amount_in_word[0]

        accountant_id = self.env['res.users'].search([('groups_id', 'in', self.env.ref('hr_employee_updation.group_accountant').id)], limit=1, order="id desc")
        if accountant_id:
            note = _('<p>%s has submitted a <span style="font-weight: bold;">Variable Increase Request: %s </span>'
                     ' and a payment request has been created on it, please view it</p>')% (accountant_id.name, self.name)
            user_id = accountant_id
            warning = ""
            date = fields.Date.today()
            activity_type = 'hr_extend.hr_request_notification'
            model = 'account.payment'
            self.notification(self.payment_id, user_id, date, activity_type, model, note, warning)

    def send_notification(self, user_id, note, warning):
        if user_id:
            notification = {
                # 'activity_type_id': self.env.ref(user_id).id,
                'res_id': self.id,
                'res_model_id': self.env['ir.model'].search([('model', '=', 'hr.variable.increase')], limit=1).id,
                # 'icon': 'fa-pencil-square-o',
                # 'date_deadline': fields.Date.today(),
                'user_id': user_id.id,
                'note': note
            }
            self.env['mail.activity'].create(notification)
        else:
            raise ValidationError(warning)




class HRVariableIncreaseLine(models.Model):
    _name = 'hr.variable.increase.line'
    _description = 'Variable Increase Line'

    @api.depends('employee_id', 'evaluation', 'increase_per_month', 'deduction_amount', 'qty')
    def _compute_totals(self):
        for rec in self:
            if rec.employee_id:
                rec.subtotal = rec.increase_per_month * rec.qty
                rec.total = rec.subtotal * (rec.evaluation / 100)
                rec.net_amount = rec.total - rec.deduction_amount

    request_id = fields.Many2one('hr.variable.increase', 'Request', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', store=True)
    name = fields.Char(string='Reference', required=True)
    increase_per_month = fields.Float('Increase Per Month')
    qty = fields.Integer('QTY', default=3)
    subtotal = fields.Float('Subtotal', compute='_compute_totals', store=True)
    evaluation = fields.Float('Evaluation (%)', default=100.0)
    total = fields.Float('Total', compute='_compute_totals', store=True)
    deduction_amount = fields.Float('Deduction')
    net_amount = fields.Float('Net', compute='_compute_totals', store=True)


class Company(models.Model):
    _inherit = 'res.company'

    increase_journal_id = fields.Many2one('account.journal', 'Variable Increase Journal')
    increase_account_id = fields.Many2one('account.account', 'Variable Increase Account')


class ResIncreaseSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    increase_journal_id = fields.Many2one('account.journal', 'Variable Increase Journal', related='company_id.increase_journal_id', readonly=False)
    increase_account_id = fields.Many2one('account.account', 'Variable Increase Account', related='company_id.increase_account_id', readonly=False)
