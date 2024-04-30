from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import timedelta


class HrContract(models.Model):
    _inherit = 'hr.contract'

    call_allowance = fields.Float('Call Allowance', default=0.0)
    food_allowance = fields.Float('Food Allowance', default=0.0)
    position_allowance = fields.Float('Position Allowance', default=0.0)

    total_wage_amount = fields.Float('Total Wage Amount', compute="compute_total_wage_amount", store=True)

    contract_type_duration = fields.Selection([
        ('3', '3 Months'),
        ('6', '6 Months'),
        ('9', '9 Months'),
        ('12', '12 Months'),
        ('15', '15 Months'),
        ('18', '18 Months'),
        ('21', '21 Months'),
        ('24', '24 Months'),
    ], string='Contract Duration')

    # contract_end_date = fields.Date(string='Contract End Date', compute='_compute_end_date', store=True)

    @api.depends('employee_id', 'wage', 'l10n_sa_housing_allowance', 'l10n_sa_transportation_allowance',
                 'l10n_sa_other_allowances',
                 'call_allowance', 'food_allowance', 'position_allowance')
    def compute_total_wage_amount(self):
        for contract in self:
            total = contract.wage
            total += contract.l10n_sa_housing_allowance
            total += contract.l10n_sa_transportation_allowance
            total += contract.l10n_sa_other_allowances
            total += contract.call_allowance
            total += contract.food_allowance
            total += contract.position_allowance
            contract.total_wage_amount = total

    @api.onchange('date_start', 'contract_type_duration')
    def _compute_end_date(self):
        for record in self:
            if record.date_start and record.contract_type_duration:
                duration = int(record.contract_type_duration)
                # Use relativedelta for adding months
                record.date_end = record.date_start + relativedelta(months=duration)
            else:
                record.date_end = False

    @api.model
    def _renew_contracts(self):
        today = fields.Date.today()
        contracts = self.search([('date_end', '=', today)])
        for contract in contracts:
            if contract.state == 'open':
                contract.date_start = fields.Date.today()

    def send_contract_end_notifications(self):
        # Define the target date range (30 days from now)
        target_date = fields.Date.today() + timedelta(days=60)

        # Search for contracts that will end in 30 days
        contracts_ending_soon = self.search([
            ('date_end', '=', target_date),
            ('state', '=', 'open')  # Assuming 'open' is the state for active contracts
        ])

        # Assuming you have a mail template set up for notifications
        # template = self.env.ref('your_module_name.contract_end_notification_email_template')

        for contract in contracts_ending_soon:
            if contract.hr_responsible_id.partner_id.email:
                self.env['mail.mail'].create({
                    'subject': f'Contract ending soon: {contract.name}',
                    'author_id': self.env.user.partner_id.id,
                    'email_from': self.env.user.partner_id.email,
                    'email_to': contract.hr_responsible_id.partner_id.email,
                    'body_html': 'Your contract will end in 60 days. Please contact HR for renewal.'
                }).send()
