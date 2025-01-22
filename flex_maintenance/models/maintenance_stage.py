from odoo import api, fields, models, _


class MaintenanceStage(models.Model):
    _inherit = 'maintenance.stage'

    repair_auto_trigger = fields.Boolean(string="Trigger From Repair")
