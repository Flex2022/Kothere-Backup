from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    # invoice_num_created_from_sale = fields.Many2one('sale.order',string='Invoice Num Created From Sale', compute='_compute_invoice_num_created_from_sale', store=True)
    # @api.depends('invoice_origin')
    # def _compute_invoice_num_created_from_sale(self):
    #     self.ensure_one()
    #     sale_order = self.line_ids.sale_line_ids.order_id
    #     invoice_count = self.env['account.move'].search_count(
    #         [('invoice_origin', '=', self.invoice_origin)])

    # Smart Button Fields
    source_Document_for_smart_button = fields.Char(string='Source Document SM')

    # Invisible Fields
    there_is_access_from_company_id = fields.Boolean(string='There Is Access From Company Id',
                                                     compute='_compute_there_is_access_from_company_id')

    # Lines Fields
    flex_deductions_ids = fields.One2many('deductions.lines', 'invoice_id', string='Deductions')
    flex_additions_ids = fields.One2many('additions.lines', 'invoice_id', string='Additions')

    # Main Amount Fields
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
    total_deductions = fields.Float('Total Deductions', compute='_compute_total_deductions', store=True)
    project_invoice_from_sale_order = fields.Many2one('project.project', string='Project Invoice',
                                                      compute='_compute_project_invoice_from_sale_order', store=True
                                                      )
    deductions_no = fields.Integer('Deductions No')

    is_out_invoice = fields.Boolean('Is Out Invoice', compute='_compute_is_out_invoice', store=False)

    @api.depends('move_type')
    def _compute_is_out_invoice(self):
        for record in self:
            if record.move_type == 'out_invoice':
                record.is_out_invoice = True
            else:
                record.is_out_invoice = False

    @api.depends('invoice_origin')
    def _compute_project_invoice_from_sale_order(self):
        for record in self:
            if record.invoice_origin:
                sale_order = self.env['sale.order'].search([('name', '=', record.invoice_origin)], limit=1)
                record.project_invoice_from_sale_order = sale_order.project_invoice.id if sale_order else False
            else:
                record.project_invoice_from_sale_order = False

    @api.depends('invoice_origin')
    def _compute_project_invoice_from_sale_order(self):
        for record in self:
            if record.invoice_origin:
                sale_order = self.env['sale.order'].search([('name', '=', record.invoice_origin)], limit=1)
                record.deductions_no = sale_order.deductions_no if sale_order else False
            else:
                record.deductions_no = False

    # smart Button Functions
    def open_created_journal(self):
        return {
            'name': 'Deductions Lines',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'domain': [('source_Document_for_smart_button', '=', self.name)],
            'context': {'default_source_Document_for_smart_button': self.name},
        }

    invoice_count = fields.Integer(compute='_compute_invoice_count', string='Journal Entres')

    def _compute_invoice_count(self):
        for record in self:
            record.invoice_count = self.env['account.move'].search_count(
                [('source_Document_for_smart_button', '=', record.name)])

    @api.depends('deductions_amount', 'additions_amount')
    def _compute_total_deductions(self):
        for rec in self:
            rec.total_deductions = rec.amount_untaxed - rec.deductions_amount + rec.additions_amount

    # Compute Functions For Check Access
    def _compute_there_is_access_from_company_id(self):
        for record in self:
            if record.move_type == 'out_invoice':
                if record.company_id.flex_additions_deductions_ids:
                    record.there_is_access_from_company_id = True
                else:
                    record.there_is_access_from_company_id = False
            else:
                record.there_is_access_from_company_id = False

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

    # Compute Functions For Amounts
    @api.depends('flex_additions_ids')
    def _compute_additions_amount(self):
        for record in self:
            record.additions_amount = sum(record.flex_additions_ids.mapped('amount'))

    def create_journal_entry_when_conferim(self):
        for record in self:
            if record.there_is_access_from_company_id:
                if record.flex_deductions_ids:
                    for line in record.flex_deductions_ids:
                        journal = self.env['account.move'].create({
                            'ref': line.name,
                            'move_type': 'entry',
                            'source_Document_for_smart_button': record.name,
                            'line_ids': [
                                (0, 0, {
                                    'name': line.name,
                                    'partner_id': record.partner_id.id,
                                    'account_id': record.partner_id.property_account_receivable_id.id,
                                    'credit': line.amount,
                                }),
                                (0, 0, {
                                    'name': line.name,
                                    'partner_id': record.partner_id.id,
                                    'account_id': line.deductions_id.account_id.id,
                                    'debit': line.amount,
                                }),
                            ],

                        }).action_post()
                if record.flex_additions_ids:
                    for line in record.flex_additions_ids:
                        journal = self.env['account.move'].create({
                            'ref': line.name,
                            'move_type': 'entry',
                            'source_Document_for_smart_button': record.name,
                            'line_ids': [
                                (0, 0, {
                                    'name': line.name,
                                    'partner_id': record.partner_id.id,
                                    'account_id': line.additions_id.account_id.id,
                                    'credit': line.amount,
                                }),
                                (0, 0, {
                                    'name': line.name,
                                    'partner_id': record.partner_id.id,
                                    'account_id': record.partner_id.property_account_receivable_id.id,
                                    'debit': line.amount,
                                }),
                            ],

                        }).action_post()

    def action_post(self):
        if self.there_is_access_from_company_id:
            self.create_journal_entry_when_conferim()
        return super(AccountMove, self).action_post()

    def button_draft(self):
        if self.there_is_access_from_company_id:
            domain = [('source_Document_for_smart_button', '=', self.name)]
            journals = self.env['account.move'].search(domain)
            for journal in journals:
                if journal.state == 'posted':
                    journal.button_draft()
        return super(AccountMove, self).button_draft()

    def set_line_number(self):
        sl_no = 0
        for line in self.invoice_line_ids:
            sl_no += 1
            line.line_number = sl_no
        return

    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)

        self.set_line_number()
        return res

    def write(self, vals):
        res = super(AccountMove, self).write(vals)
        self.set_line_number()
        return res


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    line_number = fields.Integer(string='Line Number')

    previous_accomplishment = fields.Float(string='Last Accomplishment', compute='_compute_previous_accomplishment',
                                           store=True)

    current_accomplishment = fields.Float(string='Current Accomplishment', compute='_compute_current_accomplishment',
                                          store=False)

    total_accomplishment = fields.Float(string='Total Accomplishment', compute='_compute_total_accomplishment',
                                        store=False)

    # is_out_invoice = fields.Boolean('Is Out Invoice', related='move_id.is_out_invoice')

    @api.depends('quantity', 'price_unit', 'product_id', 'move_id.deductions_no')
    def _compute_previous_accomplishment(self):
        # invoice_line = self.env['account.move.line'].search(
        #     [('product_id', '=', self.product_id.id), ('move_id', '=', self.move_id.id)])
        # for record in self:
        #     if invoice_line:
        #         record.previous_accomplishment = sum(invoice_line.mapped('quantity')) * sum(
        #             invoice_line.mapped('price_unit'))
        #     else:
        #         record.previous_accomplishment = 0.0
        for record in self:
            if record.quantity and record.price_unit and record.product_id and record.move_id.deductions_no > 0:
                # Find all invoice lines with the same product
                invoice_lines = self.env['account.move.line'].search([
                    ('product_id', '=', record.product_id.id),
                    ('move_id.deductions_no', '>', 0),
                    ('move_id.project_invoice_from_sale_order', '=', record.move_id.project_invoice_from_sale_order.id),
                ])

                # Compute the sum of quantity * price_unit for all matching invoice lines
                total_accomplishment = sum(line.quantity * line.price_unit for line in invoice_lines)

                record.previous_accomplishment = total_accomplishment
            else:
                record.previous_accomplishment = 0.0

    @api.depends('quantity', 'price_unit')
    def _compute_current_accomplishment(self):
        for record in self:
            if record.quantity and record.price_unit and record.move_id.deductions_no > 0:
                record.current_accomplishment = record.quantity * record.price_unit
            else:
                record.current_accomplishment = 0.0

    # when create new line start from one then increase by one
    # @api.depends('invoice_line_ids')

    @api.depends('previous_accomplishment', 'current_accomplishment')
    def _compute_total_accomplishment(self):
        for record in self:
            if record.previous_accomplishment and record.current_accomplishment:
                record.total_accomplishment = record.previous_accomplishment + record.current_accomplishment
            else:
                record.total_accomplishment = 0.0
