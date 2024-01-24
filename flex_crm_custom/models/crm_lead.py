from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import json


class CustomCrmLead(models.Model):
    _inherit = 'crm.lead'

    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
                                  default=lambda self: self.env.company.currency_id.id)
    order_line_ids = fields.One2many('crm.order.line', 'lead_id', string='Order Lines')
    total_order_line_ids = fields.Monetary(string='Probability', compute='_compute_total_order_lines',
                                           store=True, currency_field='company_currency', tracking=True)
    probability_order_line_active = fields.Boolean(string='Show Order Line Probability',
                                                   related="company_id.probability_order_line_active")

    project_id = fields.Many2one('project.project', string='Project', no_create=True, copy=False)



    @api.depends('order_line_ids.price_total')
    def _compute_total_order_lines(self):
        for lead in self:
            lead.total_order_line_ids = sum(lead.order_line_ids.mapped('price_total'))

    def write(self, vals):
        res = super(CustomCrmLead, self).write(vals)
        if 'stage_id' in vals:
            if vals['stage_id'].project_required:
                raise UserError(_('You must add project to this lead'))
        return res


class CrmOrderLine(models.Model):
    _name = 'crm.order.line'
    _description = 'CRM Order Line'
    _inherit = ['analytic.mixin']

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
                                  default=lambda self: self.env.company.currency_id.id)
    lead_id = fields.Many2one('crm.lead', string='Lead', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    name = fields.Char(string='Description')
    analytic_distribution_text = fields.Text(company_dependent=True)
    analytic_distribution = fields.Json(inverse="_inverse_analytic_distribution", store=False, precompute=False)
    tax_ids = fields.Many2many('account.tax', string='Taxes')
    discount = fields.Float(string='Discount (%)')
    quantity = fields.Float(string='Quantity', default=1)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    price_unit = fields.Float(string='Unit Price')
    price_subtotal = fields.Monetary(string='Tax excl.', compute='_compute_totals', store=True)
    price_total = fields.Monetary(string='Tax incl.', compute='_compute_totals', store=True)
    tax_country_id = fields.Many2one(
        comodel_name='res.country',
        related='company_id.account_fiscal_country_id',
        # Avoid access error on fiscal position, when reading a purchase order with company != user.company_ids
        compute_sudo=True,
        help="Technical field to filter the available taxes depending on the fiscal country and fiscal position.")

    @api.depends_context('company')
    @api.depends('analytic_distribution_text')
    def _compute_analytic_distribution(self):
        for record in self:
            record.analytic_distribution = json.loads(record.analytic_distribution_text or '{}')

    def _inverse_analytic_distribution(self):
        for record in self:
            record.analytic_distribution_text = json.dumps(record.analytic_distribution)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.name
            self.product_uom = self.product_id.uom_id.id
            self.price_unit = self.product_id.lst_price

    @api.depends('quantity', 'discount', 'price_unit', 'tax_ids', 'currency_id')
    def _compute_totals(self):
        for line in self:
            # Compute 'price_subtotal'.
            line_discount_price_unit = line.price_unit * (1 - (line.discount / 100.0))
            subtotal = line.quantity * line_discount_price_unit

            # Compute 'price_total'.
            if line.tax_ids:
                taxes_res = line.tax_ids.compute_all(
                    line_discount_price_unit,
                    quantity=line.quantity,
                    currency=line.currency_id,
                    product=line.product_id,
                    partner=line.lead_id.partner_id,
                )
                line.price_subtotal = taxes_res['total_excluded']
                line.price_total = taxes_res['total_included']
            else:
                line.price_total = line.price_subtotal = subtotal

class CrmStage(models.Model):
    _inherit = 'crm.stage'

    project_required = fields.Boolean(string='Project Required', default=False)
