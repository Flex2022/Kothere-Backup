from odoo import api, fields, models


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    is_attach_required = fields.Boolean(string='Attachment Required', default=False,
                                        help='If checked, employees will be required to attach a document when requesting time off of this type.')
