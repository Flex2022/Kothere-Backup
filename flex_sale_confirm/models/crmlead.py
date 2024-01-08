from odoo import fields, models, api, _


class Cmlead(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def name_get(self):
        result = []
        for rec in self:
            name = rec.name
            name = (rec.opportunity_reference if rec.opportunity_reference else name) + ' | ' + name
            result.append((rec.id, name))

        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        domain = args + ['|', ('opportunity_reference', operator, name), ('name', operator, name)]
        return super(Cmlead, self).search(domain, limit=limit).name_get()
