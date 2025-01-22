from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _rec_names_search = ['complete_name', 'email', 'ref', 'vat', 'company_registry', 'arabic_name']

    arabic_name = fields.Char(string='Arabic Name')
    partner_code = fields.Char(string="Partner Code", required=False, copy=False, readonly=True,
                           default=lambda self: _('New'))

    @api.depends('complete_name', 'email', 'vat', 'state_id', 'country_id', 'commercial_company_name')
    @api.depends_context('show_address', 'partner_show_db_id', 'address_inline', 'show_email', 'show_vat', 'lang')
    def _compute_display_name(self):
        if self.env.lang == 'ar_001':
            for partner in self:
                partner.display_name = (partner.arabic_name or partner.with_context(lang=self.env.lang)._get_complete_name()).strip()
        else:
            super(ResPartner, self)._compute_display_name()

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
                elif rec.partner_code == '':
                    rec.partner_code = self.env['ir.sequence'].next_by_code('res.partner')
                elif rec.partner_code == False:
                    rec.partner_code = self.env['ir.sequence'].next_by_code('res.partner')

