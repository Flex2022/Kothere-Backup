# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import AccessError


class PurchaseType(models.Model):
    _name = 'purchase.type'
    _description = 'Purchase Type'

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, access_rights_uid=None):
        if not domain:
            domain = []
        current_user = self.env.user
        if current_user.allowed_purchase_types and not self._context.get('force_list_all', False):
            domain += [('id', 'in', current_user.allowed_purchase_types.ids)]
        return super(PurchaseType, self)._search(domain, offset=offset, limit=limit, order=order, access_rights_uid=access_rights_uid)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        current_user = self.env.user
        if current_user.allowed_purchase_types and not self._context.get('force_list_all', False):
            if not domain:
                domain = []
            domain += [('id', 'in', current_user.allowed_purchase_types.ids)]
        return super(PurchaseType, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

    @api.model
    def _check_can_read(self):
        """ Restricts the access """
        if self.env.is_superuser():
            return True
        current_user = self.env.user
        if current_user.allowed_purchase_types and not self._context.get('force_list_all', False):
            purchase_types = current_user.allowed_purchase_types.ids
            # if any(rec.id not in purchase_types for rec in self.sudo()):
            for rec in self.sudo():
                if rec.id not in purchase_types:
                    raise AccessError(_("Sorry, you are not allowed to access records for (%s): \n- %s")
                                      % (rec._name, rec.name))

    def _read(self, fields):
        self._check_can_read()
        return super(PurchaseType, self)._read(fields)
