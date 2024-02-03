from odoo import api, fields, models

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



    @api.onchange('appointment_type')
    def _onchange_appointment_type(self):
        if self.appointment_type == 'external':
            self.is_external = False
        else:
            self.is_external = True
