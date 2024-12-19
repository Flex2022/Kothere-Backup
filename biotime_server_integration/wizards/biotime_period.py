# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta


class BiotimePeriod(models.TransientModel):
    _name = 'biotime.period'
    _description = 'Biotime Period Wizard'

    # def _yesterday(self):
    #     return (fields.Date.today() + relativedelta(days=-1))

    # date_from = fields.Date(string='From Date', default=_yesterday)
    date_from = fields.Date(string='From Date', default=fields.Date.today())
    date_to = fields.Date(string='To Date', default=fields.Date.today())
    biotime_server_id = fields.Many2one('biotime.server', string='Biotime Server')
    method_name = fields.Selection(
        selection=[
            ('download_transactions', 'download_transactions'),
            ('download_generate_attendances', 'download_generate_attendances'),
        ],
        string='Method Name'
    )

    @api.constrains('date_from', 'date_to')
    def check_dates(self):
        if self.filtered(lambda wiz: wiz.date_from and wiz.date_to and wiz.date_from > wiz.date_to):
            raise UserError(_('To Date must be after From Date'))

    def action_confirm(self):
        date_from = self.date_from.strftime('%Y-%m-%d')
        date_to = self.date_to.strftime('%Y-%m-%d')
        if self.method_name == 'download_transactions':
            self.biotime_server_id.download_transactions(date_from=date_from, date_to=date_to)
        elif self.method_name == 'download_generate_attendances':
            self.biotime_server_id.download_generate_attendances(date_from=date_from, date_to=date_to)

