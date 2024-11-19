from odoo import api, fields, models, Command


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # NEW EDITS.
    # Start
    flex_deductions_ids = fields.One2many('deductions.lines', 'order_id', string='Deductions')
    flex_additions_ids = fields.One2many('additions.lines', 'order_id', string='Additions')
    there_is_access_from_company_id = fields.Boolean('There is Access from Company',
                                                     compute='_compute_there_is_access_from_company_id')

    deductions_amount = fields.Float('Deductions Amount', compute='_compute_deductions_amount', store=True)
    additions_amount = fields.Float('Additions Amount', compute='_compute_additions_amount', store=True)

    # Sub Type Amount Fields
    deductions_amount_type_discounts = fields.Float('Discounts', compute='_compute_deductions_amount', store=True)
    deductions_amount_type_insurances = fields.Float('Insurances', compute='_compute_deductions_amount', store=True)
    deductions_amount_type_advance_payment = fields.Float('Advance Payment', compute='_compute_deductions_amount',
                                                          store=True)
    deductions_amount_type_business_guarantee = fields.Float('Business Guarantee', compute='_compute_deductions_amount',
                                                             store=True)

    # sum
    total_deductions = fields.Float('Total value of the extract', compute='_compute_total_deductions', store=True)
    all_total_deductions = fields.Float('total value of what is due, including value-added tax',
                                        compute='_compute_total_deductions', store=True)

    @api.depends('flex_deductions_ids')
    def _compute_deductions_amount(self):
        for record in self:
            record.deductions_amount = sum(record.flex_deductions_ids.mapped('amount'))
            case_1 = self.env['deductions.lines'].search(
                [('invoice_id', '=', record.id), ('deductions_id.type_deductions', '=', '1')])
            record.deductions_amount_type_discounts = sum(case_1.mapped('amount'))
            case_2 = self.env['deductions.lines'].search(
                [('invoice_id', '=', record.id), ('deductions_id.type_deductions', '=', '2')])
            record.deductions_amount_type_insurances = sum(case_2.mapped('amount'))
            case_3 = self.env['deductions.lines'].search(
                [('invoice_id', '=', record.id), ('deductions_id.type_deductions', '=', '3')])
            record.deductions_amount_type_advance_payment = sum(case_3.mapped('amount'))
            case_4 = self.env['deductions.lines'].search(
                [('invoice_id', '=', record.id), ('deductions_id.type_deductions', '=', '4')])
            record.deductions_amount_type_business_guarantee = sum(case_4.mapped('amount'))

    @api.depends('flex_additions_ids')
    def _compute_additions_amount(self):
        for record in self:
            record.additions_amount = sum(record.flex_additions_ids.mapped('amount'))
    @api.depends('deductions_amount', 'additions_amount', 'amount_untaxed')
    def _compute_total_deductions(self):
        for rec in self:
            rec.total_deductions = rec.amount_untaxed - rec.deductions_amount + rec.additions_amount
            rec.all_total_deductions = rec.amount_untaxed - rec.deductions_amount + rec.additions_amount + rec.amount_tax


    def _compute_there_is_access_from_company_id(self):
        for record in self:
            if record.company_id.flex_additions_deductions_ids:
                record.there_is_access_from_company_id = True
            else:
                record.there_is_access_from_company_id = False

    # End

    project_invoice = fields.Many2one('project.project', string='Project Invoice')

    project_manager = fields.Many2one('res.partner', string='Project Manager')

    projects_manager = fields.Many2one('res.partner', string='Projects Manager')

    deductions_no = fields.Integer('Deductions No', default=0)

    def set_line_number(self):
        # every time click on set line number deductions_no will be incremented by 1
        for record in self:
            record.deductions_no += 1
            record.write({'deductions_no': record.deductions_no})

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        self.set_line_number()
        return res

    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()

        values = {
            'ref': self.client_order_ref or '',
            'move_type': 'out_invoice',
            'narration': self.note,
            'currency_id': self.currency_id.id,
            'campaign_id': self.campaign_id.id,
            'medium_id': self.medium_id.id,
            'source_id': self.source_id.id,
            'team_id': self.team_id.id,
            'partner_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id._get_fiscal_position(
                self.partner_invoice_id)).id,
            'invoice_origin': self.name,
            'invoice_payment_term_id': self.payment_term_id.id,
            'invoice_user_id': self.user_id.id,
            'payment_reference': self.reference,
            'transaction_ids': [Command.set(self.transaction_ids.ids)],
            'company_id': self.company_id.id,
            'invoice_line_ids': [],
            'user_id': self.user_id.id,
            'project_invoice_from_sale_order': self.project_invoice.id,
            'flex_deductions_ids': [(0, 0, {
                'name': line.name,
                'deductions_id': line.deductions_id.id,
                'is_percentage': line.is_percentage,
                'percentage_or_value': line.percentage_or_value,
                'tax_id': line.tax_id.id,
            }) for line in self.flex_deductions_ids],
            'flex_additions_ids': [(0, 0, {
                'name': line.name,
                'additions_id': line.additions_id.id,
                'is_percentage': line.is_percentage,
                'percentage_or_value': line.percentage_or_value,
                'tax_id': line.tax_id.id,
            }) for line in self.flex_additions_ids],
            'sale_employee_id': self.sale_employee_id.id,
        }
        if self.journal_id:
            values['journal_id'] = self.journal_id.id
        return values