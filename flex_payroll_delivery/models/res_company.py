from odoo import api, fields, models

class ResCompany(models.Model):
    _inherit = 'res.company'

    apply_distance = fields.Boolean(
        string='Apply Distance Per KM',
        default=False,
        help="Enable to apply distance Per Km."
    )


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    apply_distance = fields.Boolean(
        string='Apply Distance Per KM',
        related="company_id.apply_distance",
        readonly=False,
        help="Enable to apply distance Per Km."
    )