from datetime import date

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.exceptions import ValidationError

class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    appointment_type = fields.Selection([
        ('external', 'External'),
        ('internal', 'Internal'),
    ], string='Appointment Type', default='internal')

    is_external = fields.Boolean(string='Is External', default=False)

    visa_status = fields.Selection([
        ('available', 'Available'),
        ('not_available', 'Not Available'),
    ], string='Visa Status', default='available')

    job_offer_is_sent = fields.Boolean(string='Job Offer is Sent', default=False)

    receiving_the_visa = fields.Boolean(string='Receiving the Visa', default=False)

    medical_examination_date = fields.Date(string='Medical Examination Date')
    flight_tickets_booking_date = fields.Date(string='Flight Tickets Booking Date')
    quarantine_date = fields.Date(string='Quarantine Date')

    visa_expiry_date = fields.Date(string='Visa Expiry Date')
    # Date of residence
    date_of_residence = fields.Date(string='Date of Residence')

    # Nationality
    nationality = fields.Many2one('res.country', string='Nationality')


    @api.onchange('visa_expiry_date')
    def _onchange_visa_status(self):
        today = fields.Date.today()
        after_six_month = today + relativedelta(months=6)
        # print(after_six_month, self.visa_expiry_date)
        if isinstance(self.visa_expiry_date, date) and isinstance(after_six_month, date):
            # if self.visa_expiry_date < after_six_month:
            if self.visa_expiry_date < after_six_month:
                raise ValidationError('Visa Expiry Date must be more than 6 month')

    @api.onchange('date_of_residence')
    def _onchange_date_of_residence(self):
        today = fields.Date.today()
        after_90_days = today + relativedelta(days=90)
        if isinstance(self.visa_expiry_date, date) and isinstance(after_90_days, date):
            if self.date_of_residence < after_90_days:
                raise ValidationError('Date of Residence must be more than 90 days')





    @api.onchange('appointment_type')
    def _onchange_appointment_type(self):
        if self.appointment_type == 'external':
            self.is_external = False
        else:
            self.is_external = True
