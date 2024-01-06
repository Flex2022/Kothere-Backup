# -*- coding: utf-8 -*-


from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import time


class SaleOrder(models.Model):
    _inherit = "sale.order",

    state = fields.Selection(
        selection_add=[('submit', 'Submit'), ('finance', 'Sales Manager'), ('gm', 'GM Manager'), ('sale',)],
        ondelete={'pre_confirm': lambda recs: recs.write({'state': 'draft'})})
    is_company = fields.Boolean(string='Is Alayan Company', related='company_id.is_alayan')

    # po_version = fields.Integer(string='Version', default=0)
    # sq_name = fields.Char(string='SQ Sequence', copy=False)
    # add opportunity number
    # opportunity_number = fields.Char(string='Opportunity Reference', related='opportunity_id.opportunity_reference')
    # add quotation number
    # quotation_number = fields.Char(string='Quotation Reference', related='sq_name')

    # @api.onchange('is_company')
    # def onchange_is_company(self):
    #     self.is_company = self.env.company.is_alayan

    def action_submit(self):
        self.env['mail.mail'].sudo().create({
            'subject': 'Sale Order Submitted for Sales Manager Approval',
            'body_html': 'Sale Order Submitted for Sales Manager Approval',
            'email_to': ','.join(map(str, self.env.ref('flex_sale_confirm.group_sale_finance').users.mapped('email'))),

        })

        self.filtered(lambda so: so.state in ['draft', 'sent', ]).write({'state': 'submit'})

    def action_finance(self):
        self.env['mail.mail'].sudo().create({
            'subject': 'Sale Order Finance for GM Manager Approval',
            'body_html': 'Sale Order Finance for GM Manager Approval',
            'email_to': ','.join(map(str, self.env.ref('flex_sale_confirm.group_sale_gm').users.mapped('email'))),

        })
        self.filtered(lambda so: so.state in ['submit']).write({'state': 'finance'})

    def action_gm(self):
        self.filtered(lambda so: so.state in ['finance']).write({'state': 'gm'})

    def _can_be_confirmed(self):
        self.ensure_one()
        return self.state in {'draft', 'sent', 'gm'}

    def action_confirm2(self):
        res = super(SaleOrder, self).action_confirm()
        #     if not self.env.user.has_group('flex_sale_confirm.group_sale_confirm'):
        #         raise UserError(_('You don\'t have the permission to confirm sale orders'))
        #     for order in self:
        #         order.sq_name = order.name
        #         order.name = self.env['ir.sequence'].next_by_code('sale.order.so') or order.sq_name

        # Archive Template Product
        # for order in self:
        #     for line in order.order_line:
        #         if line.product_id.product_tmpl_id.product_tmp_mrp_order:
        #             line.product_id.product_tmpl_id.active = False
        return res

    # def action_draft(self):
    #     for order in self:
    #         order.po_version += 1
    #     return super(SaleOrder, self).action_draft()

# class AccountAsset(models.Model):
#     _inherit = 'account.asset'
#
#     @api.onchange('model_id')
#     def _onchange_model_id(self):
#         model = self.model_id
#         if model:
#             self.method = model.method
#             self.method_number = model.method_number
#             self.method_period = model.method_period
#             self.method_progress_factor = model.method_progress_factor
#             self.prorata = model.prorata
#             self.prorata_date = fields.Date.today()
#             self.account_analytic_id = model.account_analytic_id.id
#             self.analytic_tag_ids = [(6, 0, model.analytic_tag_ids.ids)]
#             self.account_asset_id = model.account_asset_id
#             self.account_depreciation_id = model.account_depreciation_id
#             self.account_depreciation_expense_id = model.account_depreciation_expense_id
#             self.journal_id = model.journal_id
