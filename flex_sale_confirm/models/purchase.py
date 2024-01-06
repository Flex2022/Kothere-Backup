# -*- coding: utf-8 -*-
from builtins import map

from odoo import fields, models, api, _, SUPERUSER_ID
# from odoo.exceptions import UserError, ValidationError
from lxml import etree
import json


class PurchaseOrder(models.Model):
    _inherit = "purchase.order",

    state = fields.Selection(
        selection_add=[('submit', 'Submit'), ('finance', 'Finance'), ('gm', 'GM'), ('to approve',)],
        ondelete={'submit': 'set default', 'finance': 'set default', 'gm': 'set default'})
    po_version = fields.Integer(string='Version', default=0)
    # po_name = fields.Char(string='PO Ref')
    rfq_name = fields.Char(string='RFQ Sequence', copy=False)
    vendor_type = fields.Selection([('local', 'Local Vendor'), ('international', 'International Vendor')],
                                   string="Vendor Type", compute='_compute_vendor_type', store=True)

    @api.depends('partner_id.vendor_type', 'partner_id.supplier')
    def _compute_vendor_type(self):
        for rec in self:
            if not rec.partner_id.supplier:
                rec.vendor_type = 'local'
            else:
                rec.vendor_type = rec.partner_id.vendor_type

    def button_approve(self):
        for order in self.filtered(lambda order: order._approval_allowed() and not order.rfq_name):
            if order.partner_id.vendor_type == 'international':
                order.rfq_name = order.name
                order.name = self.env['ir.sequence'].next_by_code('foreign.purchase.order') or order.rfq_name
            else:
                order.rfq_name = order.name
                order.name = self.env['ir.sequence'].next_by_code('local.purchase.order') or order.rfq_name
        return super(PurchaseOrder, self).button_approve()

    def action_submit(self):
        purchase = self.filtered(lambda po: po.state in ['draft', 'sent', ])
        purchase.write({'state': 'submit'})

        def send_mail():
            if self.env.uid == SUPERUSER_ID:
                return
            else:
                self.env['mail.mail'].sudo().create({
                    'subject': 'Purchase Order Submitted for Finance Approval',
                    'body_html': 'Purchase Order Submitted for Finance Approval',
                    'email_to': ','.join(
                        map(str, self.env.ref('flex_sale_confirm.group_purchase_finance').users.mapped('email'))),

                })

        return send_mail()

    def action_finance(self):
        purchase = self.filtered(lambda po: po.state in ['submit'])
        purchase.write({'state': 'finance'})

        def send_mail():
            if self.env.uid == SUPERUSER_ID:
                return
            else:

                self.env['mail.mail'].sudo().create({
                    'subject': 'Purchase Order Finance for GM Approval',
                    'body_html': 'Purchase Order Finance for GM Approval ',
                    'email_to': ','.join(
                        map(str, self.env.ref('flex_sale_confirm.group_purchase_gm').users.mapped('email'))),

                })

                print(','.join(map(str, self.env.ref('flex_sale_confirm.group_purchase_gm').users.mapped('email'))))

        return send_mail()

    def action_gm(self):
        purchase = self.filtered(lambda po: po.state in ['finance'])
        purchase.write({'state': 'gm'})

    def button_confirm(self):
        for order in self:
            if order.state not in ['gm']:
                continue
            order._add_supplier_to_product()
            if order._approval_allowed():
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        return True

    def button_draft(self):
        for order in self:
            order.po_version += 1
        return super(PurchaseOrder, self).button_draft()

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(PurchaseOrder, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                            submenu=submenu)
        prevent_local = not self.env.user.has_group('flex_sale_confirm.group_local_vendor')
        prevent_international = not self.env.user.has_group('flex_sale_confirm.group_international_vendor')
        if view_type == 'form' and (prevent_local or prevent_international):
            doc = etree.XML(result['arch'])
            domain = [('supplier', '=', True)]
            if prevent_local:
                domain += [('vendor_type', '!=', 'local')]
            if prevent_international:
                domain += [('vendor_type', '!=', 'international')]
            for node in doc.xpath("//field[@name='partner_id']"):
                node.set("domain", f"{domain}")
            result['arch'] = etree.tostring(doc, encoding='unicode')
        return result
