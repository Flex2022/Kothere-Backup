from datetime import timedelta

from odoo import api, fields, models


class NewModule(models.Model):
    _inherit = 'hr.employee'

    mcj = fields.Char(string="MCJ")
    iqama_id = fields.Char(string="Iqama ID")
    end_of_iqama = fields.Date(string="End of Iqama")

    type_of_insurance = fields.Char(string="Type Of Insurance")
    bank_name = fields.Char(string="Bank")
    bank_number = fields.Char(string="Bank Number")
    identification_expiry = fields.Date(string="Identification Expiry")
    passport_expiry = fields.Date(string="Passport Expiry")
    contract_hr_person = fields.Many2one('res.users', string="HR Person",related='contract_id.hr_responsible_id')



    # def notify_iqama_expiry(self):
    #     for record in self:
    #         if record.end_of_iqama and fields.Date.today() < record.end_of_iqama <= fields.Date.today() + timedelta(days=30):
    #             self.env['mail.mail'].sudo().create({
    #                 'subject': 'Iqama Expiry Notification',
    #                 'body_html': f'<p>Dear {record.name},</p><p>Your iqama will expire on {record.end_of_iqama}.</p>',
    #                 'email_to': record.work_email,
    #                 'email_cc': record.parent_id.work_email if record.parent_id else '',
    #             })
    #
    # def notify_passport_expiry(self):
    #     for record in self:
    #         if record.passport_expiry and fields.Date.today() < record.passport_expiry <= fields.Date.today() + timedelta(days=60):
    #             self.env['mail.mail'].sudo().create({
    #                 'subject': 'Passport Expiry Notification',
    #                 'body_html': f'<p>Dear {record.name},</p><p>Your passport will expire on {record.passport_expiry}.</p>',
    #                 'email_to': record.work_email,
    #                 'email_cc': record.parent_id.work_email if record.parent_id else '',
    #             })

    def notify_iqama_expiry(self):
        for record in self:
            if record.end_of_iqama and fields.Date.today() < record.end_of_iqama <= fields.Date.today() + timedelta(
                    days=30):
                email_cc = ','.join(filter(None, [
                    record.parent_id.work_email if record.parent_id else '',
                    record.contract_hr_person.partner_id.email if record.contract_hr_person and record.contract_hr_person.partner_id else ''
                ]))
                self.env['mail.mail'].sudo().create({
                    'subject': 'Iqama Expiry Notification',
                    'body_html': f'<p>Dear {record.name},</p><p>Your iqama will expire on {record.end_of_iqama}.</p>',
                    'email_to': record.work_email,
                    'email_cc': email_cc,
                })

    def notify_passport_expiry(self):
        for record in self:
            if record.passport_expiry and fields.Date.today() < record.passport_expiry <= fields.Date.today() + timedelta(
                    days=60):
                email_cc = ','.join(filter(None, [
                    record.parent_id.work_email if record.parent_id else '',
                    record.contract_hr_person.partner_id.email if record.contract_hr_person and record.contract_hr_person.partner_id else ''
                ]))
                self.env['mail.mail'].sudo().create({
                    'subject': 'Passport Expiry Notification',
                    'body_html': f'<p>Dear {record.name},</p><p>Your passport will expire on {record.passport_expiry}.</p>',
                    'email_to': record.work_email,
                    'email_cc': email_cc,
                })

    def cron_notify_expiry(self):
        employees = self.env['hr.employee'].search([])
        for employee in employees:
            employee.notify_iqama_expiry()
            employee.notify_passport_expiry()


