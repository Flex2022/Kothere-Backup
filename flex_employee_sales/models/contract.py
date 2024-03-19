from odoo import api, fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'


    def update_l10n_sa_number_of_days(self):
        for contract in self:
            if contract.employee_id and contract.date_start and contract.state == 'open':
                to_day = fields.Date.today()
                count_of_years = to_day.year - contract.date_start.year
                if count_of_years >= 5:
                    contract.l10n_sa_number_of_days = 30
                else:
                    contract.l10n_sa_number_of_days = 15

    def cron_job_update_l10n_sa_number_of_days(self):
        contracts = self.env['hr.contract'].search([('state', '=', 'open')])
        for contract in contracts:
            if contract.state == 'open':
                contract.update_l10n_sa_number_of_days()

