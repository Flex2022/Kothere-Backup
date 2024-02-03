from odoo import api, fields, models


CATEGORY_SELECTION = [
    ('required', 'Required'),
    ('optional', 'Optional'),
    ('no', 'None')]


class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    has_appointment_type = fields.Selection(CATEGORY_SELECTION, string="Has type of appointment", default="no", required=True)


class ApprovalRequest(models.Model):

    _inherit = 'approval.request'
    has_appointment_type = fields.Selection(related="category_id.has_appointment_type")

    appointment_type = fields.Selection([
        ('external', 'External'),
        ('internal', 'Internal'),], string="Appointment Type",)

    # def _prepare_approval_request(self, request):
    #     res = super(ApprovalRequest, self)._prepare_approval_request(request)
    #     res['appointment_type'] = request.get('appointment_type', False)
    #     return res