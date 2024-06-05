from odoo import fields, models, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    project_invoice = fields.Many2one('project.project', string='Project Invoice')

    project_manager = fields.Many2one('res.partner', string='Project Manager')

    projects_manager = fields.Many2one('res.partner', string='Projects Manager')

