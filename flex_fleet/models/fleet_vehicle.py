from datetime import timedelta

from odoo import api, fields, models


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    date_of_examination = fields.Date(string='Date of Examination', tracking=True)
    insurance_date = fields.Date(string='Insurance date', tracking=True)
    operation_date = fields.Date(string='Operation date', tracking=True)
    periodic_inspection = fields.Date(string='Periodic Inspection', tracking=True)
    responsable_log_contract = fields.Many2one('res.users', string="Responsible", compute='_compute_responsable_log_contract', store=True,tracking=True)


    @api.depends('log_contracts')
    def _compute_responsable_log_contract(self):
        #will log_contracts is one2many field whice need that to bring last log_contracts user_id
        for record in self:
            if record.log_contracts:
                record.responsable_log_contract = record.log_contracts[-1].user_id
            else:
                record.responsable_log_contract = False



    def notify_insurance_date(self):
        for record in self:
            if record.insurance_date and fields.Date.today() < record.insurance_date <= fields.Date.today() + timedelta(
                    days=90):
                email_cc = ','.join(filter(None, [
                    record.manager_id.login if record.manager_id else '',
                    record.responsable_log_contract.partner_id.email if record.responsable_log_contract else '',
                ]))
                name = ','.join(filter(None, [
                    record.manager_id.name if record.manager_id else '',
                    record.responsable_log_contract.partner_id.name if record.responsable_log_contract else '',
                ]))
                self.env['mail.mail'].sudo().create({
                    'subject': 'Insurance Date Notification',
                    'body_html': f'<p>Dear {name},</p><p>vehicle model {record.name} insurance date will expire on {record.insurance_date}.</p>',
                    'email_to': email_cc
                    # 'email_cc': email_cc,
                })

    #same for operation_date and periodic_inspection
    def notify_operation_date(self):
        for record in self:
            if record.operation_date and fields.Date.today() < record.operation_date <= fields.Date.today() + timedelta(
                    days=90):
                email_cc = ','.join(filter(None, [
                    record.manager_id.login if record.manager_id else '',
                    record.responsable_log_contract.partner_id.email if record.responsable_log_contract else '',
                ]))
                name = ','.join(filter(None, [
                    record.manager_id.name if record.manager_id else '',
                    record.responsable_log_contract.partner_id.name if record.responsable_log_contract else '',
                ]))
                self.env['mail.mail'].sudo().create({
                    'subject': 'Operation Date Notification',

                    'body_html': f'<p>Dear {name},</p><p>vehicle model {record.name} operation date will expire on {record.operation_date}.</p>',
                    'email_to': email_cc
                    # 'email_cc': email_cc,
                })

    def notify_periodic_inspection(self):
        for record in self:
            if record.periodic_inspection and fields.Date.today() < record.periodic_inspection <= fields.Date.today() + timedelta(
                    days=90):
                email_cc = ','.join(filter(None, [
                    record.manager_id.login if record.manager_id else '',
                    record.responsable_log_contract.partner_id.email if record.responsable_log_contract else '',
                ]))
                name = ','.join(filter(None, [
                    record.manager_id.name if record.manager_id else '',
                    record.responsable_log_contract.partner_id.name if record.responsable_log_contract else '',
                ]))
                self.env['mail.mail'].sudo().create({
                    'subject': 'Periodic Inspection Notification',
                    'body_html': f'<p>Dear {name},</p><p>vehicle model {record.name} periodic inspection will expire on {record.periodic_inspection}.</p>',
                    'email_to': email_cc
                    # 'email_cc': email_cc,
                })



    def cron_notify_expiry(self):
        fleets = self.env['fleet.vehicle'].search([])
        for fleet in fleets:
            fleet.notify_insurance_date()
            fleet.notify_operation_date()
            fleet.notify_periodic_inspection()


