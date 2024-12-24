# -*- coding: utf-8 -*-
from odoo import fields, models, api, _, SUPERUSER_ID
# from odoo.exceptions import UserError, ValidationError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    purchase_type_id = fields.Many2one(comodel_name='purchase.type', string='Purchase Type')

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, access_rights_uid=None):
        if not domain:
            domain = []
        current_user = self.env.user
        if current_user.allowed_purchase_types and not self._context.get('force_list_all', False):
            domain += [('purchase_type_id', 'in', current_user.allowed_purchase_types.ids + [False])]
        return super(PurchaseOrder, self)._search(domain, offset=offset, limit=limit, order=order, access_rights_uid=access_rights_uid)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        current_user = self.env.user
        if current_user.allowed_purchase_types and not self._context.get('force_list_all', False):
            if not domain:
                domain = []
            domain += [('purchase_type_id', 'in', current_user.allowed_purchase_types.ids + [False])]
        return super(PurchaseOrder, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

    @api.model
    def _check_can_read(self):
        """ Restricts the access """
        if self.env.is_superuser():
            return True
        current_user = self.env.user
        if current_user.allowed_purchase_types and not self._context.get('force_list_all', False):
            purchase_types = current_user.allowed_purchase_types.ids + [False]
            # if any(rec.id not in purchase_types for rec in self.sudo()):
            for rec in self.sudo():
                if rec.purchase_type_id.id not in purchase_types:
                    raise PurchaseOrder(_("Sorry, you are not allowed to access records for (%s): \n- %s")
                                      % (rec._name, rec.name))

    def _read(self, fields):
        self._check_can_read()
        return super(PurchaseOrder, self)._read(fields)

