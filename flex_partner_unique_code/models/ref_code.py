from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # partner_code = fields.Char(string="Partner Code", unique=True)

    @api.constrains('ref')
    def _check_ref_unique(self):
        for partner in self:
            if partner.ref:
                duplicates = self.search([('ref', '=', partner.ref), ('id', '!=', partner.id)], limit=1)
                if duplicates:
                    raise ValidationError(_("Ref code must be unique!"))

