from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_code = fields.Char(string="Partner Code", unique=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('partner_code', _('New')) == _('New'):
                    vals['partner_code'] = self.env['ir.sequence'].next_by_code('res.partner')
        return super(ResPartner, self).create(vals_list)

    def random_sequence(self):
        for rec in self:
            if rec.active:
                if rec.partner_code == _('New'):
                    rec.partner_code = self.env['ir.sequence'].next_by_code('res.partner')

