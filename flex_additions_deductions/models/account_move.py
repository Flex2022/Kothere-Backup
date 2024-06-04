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
    deductions_amount_type_final_guarantee = fields.Float('Final Guarantee', compute='_compute_deductions_amount',
                                                          store=True)

    # sum
    total_deductions = fields.Float('Total value of the extract', compute='_compute_total_deductions', store=True)
    all_total_deductions = fields.Float('total value of what is due, including value-added tax',
                                        compute='_compute_total_deductions', store=True)
    project_invoice_from_sale_order = fields.Many2one('project.project', string='Project Invoice',
                                                      compute='_compute_project_invoice_from_sale_order', store=True
                                                      )
    deductions_no = fields.Integer('Deductions No', compute='_compute_origin_deductions_no_count', store=True)

    is_out_invoice = fields.Boolean('Is Out Invoice', compute='_compute_is_out_invoice', store=False)

    contract_amount = fields.Float(string='Contract Amount', compute='_compute_contract_amount', store=False)

    project_manager = fields.Many2one('res.partner', string='Project Manager',
                                      compute='_compute_project_manager', store=True)
    projects_manager = fields.Many2one('res.partner', string='Projects Manager',
                                       compute='_compute_projects_manager', store=True)

    # @api.depends('line_ids.sale_line_ids')
    # def _compute_origin_deductions_no_count(self):
    #     for move in self:
    #         # print(move.invoice_origin)
    #         # order_id = move.line_ids.sale_line_ids.order_id
    #         # move.deductions_no = len(order_id.invoice_ids)
    #         count = 1
    #         sort_invoice_by_created_date = self.env['account.move'].search(
    #                 [('invoice_origin', '=', move.invoice_origin), ('move_type', '=', 'out_invoice')],
    #                 order='create_date asc')
    #         for invoice in sort_invoice_by_created_date:
    #             invoice.deductions_no = count
    #             count += 1

    @api.depends('line_ids.sale_line_ids')
    def _compute_origin_deductions_no_count(self):
        for move in self:
            count = 0
            # Retrieve all invoices related to the current move, sorted by creation date
            invoices = self.env['account.move'].search([
                ('invoice_origin', '=', move.invoice_origin),
                ('move_type', '=', 'out_invoice')
            ], order='create_date asc')

            # Iterate through each invoice and count them
            for invoice in invoices:
                count += 1

            # Update the deductions_no field of the current move with the count
            move.deductions_no = count

    @api.depends('invoice_origin')
    def _compute_project_manager(self):
        for record in self:
            if record.invoice_origin:
                sale_order = self.env['sale.order'].search([('name', '=', record.invoice_origin)], limit=1)
                purchase_order = self.env['purchase.order'].search([('name', '=', record.invoice_origin)], limit=1)
                if sale_order:
                    record.project_manager = sale_order.project_manager.id
                if purchase_order:
                    record.project_manager = purchase_order.project_manager.id
            else:
                record.project_manager = False

    @api.depends('invoice_origin')
    def _compute_projects_manager(self):
        for record in self:
            if record.invoice_origin:
                sale_order = self.env['sale.order'].search([('name', '=', record.invoice_origin)], limit=1)
                purchase_order = self.env['purchase.order'].search([('name', '=', record.invoice_origin)], limit=1)
                if sale_order:
                    record.projects_manager = sale_order.projects_manager.id
                if purchase_order:
                    record.projects_manager = purchase_order.projects_manager.id
            else:
                record.projects_manager = False

    @api.depends('move_type')
    def _compute_is_out_invoice(self):
        for record in self:
            if record.move_type == 'out_invoice':
                record.is_out_invoice = True
            else:
                record.is_out_invoice = False

    # @api.depends('invoice_origin')
    # def _compute_contract_amount(self):
    #     for record in self:
    #         if record.invoice_origin:
    #             sale_order = self.env['sale.order'].search([('name', '=', record.invoice_origin)], limit=1)
    #             record.contract_amount = sale_order.amount_total if sale_order else False
    #         else:
    #             record.contract_amount = False

    @api.depends('invoice_origin')
    def _compute_contract_amount(self):
        for record in self:
            record.contract_amount = 0.0
            # if record.invoice_origin:
            #     sale_order = self.env['sale.order'].search([('name', '=', record.invoice_origin)], limit=1)
            #     if sale_order:
            #         record.contract_amount = float(sale_order.amount_total)

    # @api.depends('invoice_origin')
    # def _compute_project_invoice_from_sale_order(self):
    #     for record in self:
    #         if record.invoice_origin:
    #             sale_order = self.env['sale.order'].search([('name', '=', record.invoice_origin)], limit=1)
    #             record.project_invoice_from_sale_order = sale_order.project_invoice.id if sale_order else False
    #         else:
    #             record.project_invoice_from_sale_order = False
    #
    @api.depends('invoice_origin')
    def _compute_project_invoice_from_sale_order(self):
        for record in self:
            record.project_invoice_from_sale_order = False
            if record.invoice_origin:
                sale_order = self.env['sale.order'].search([('name', '=', record.invoice_origin)], limit=1)
                purchase_order = self.env['purchase.order'].search([('name', '=', record.invoice_origin)], limit=1)
                if sale_order:
                    record.project_invoice_from_sale_order = sale_order.project_invoice.id
                elif purchase_order:
                    record.project_invoice_from_sale_order = purchase_order.project_invoice.id

    # @api.depends('invoice_origin')
    # def _compute_project_invoice_from_sale_order(self):
    #     for record in self:
    #         if record.invoice_origin:
    #             sale_order = self.env['sale.order'].search([('name', '=', record.invoice_origin)], limit=1)
    #             record.deductions_no = sale_order.deductions_no if sale_order else False
    #         else:
    #             record.deductions_no = False

    # smart Button Functions
    def open_created_journal(self):
        tree_view_id = self.env.ref('account.view_move_tree').id
        return {
            'name': 'Deductions Lines',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree')],
            'domain': [('source_Document_for_smart_button', '=', self.name), ('move_type', '=', 'entry')],
            'context': {'default_source_Document_for_smart_button': self.name,
                        'default_move_type': 'entry'
                        },
        }

    invoice_count = fields.Integer(compute='_compute_invoice_count', string='Journal Entres')

    def _compute_invoice_count(self):
        for record in self:
            record.invoice_count = self.env['account.move'].search_count(
                [('source_Document_for_smart_button', '=', record.name)])

    @api.depends('deductions_amount', 'additions_amount', 'amount_untaxed')
    def _compute_total_deductions(self):
        for rec in self:
            rec.total_deductions = rec.amount_untaxed - rec.deductions_amount + rec.additions_amount
            rec.all_total_deductions = rec.amount_untaxed - rec.deductions_amount + rec.additions_amount + rec.amount_tax

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
            case_5 = self.env['deductions.lines'].search(
                [('invoice_id', '=', record.id), ('deductions_id.type_deductions', '=', '5')])
            record.deductions_amount_type_final_guarantee = sum(case_5.mapped('amount'))

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
        res = super(AccountMove, self).action_post()
        if self.there_is_access_from_company_id:
            self.create_journal_entry_when_conferim()
        return res

    def button_draft(self):
        if self.there_is_access_from_company_id:
            domain = [('source_Document_for_smart_button', '=', self.name)]
            journals = self.env['account.move'].search(domain)
            for journal in journals:
                if journal.state == 'posted':
                    journal.button_draft()
                    journal.button_cancel()
                if journal.state == 'draft':
                    journal.button_cancel()
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
        for record in self:
            if record.move_id.deductions_no == 1:
                record.previous_accomplishment = 0.0
            else:
                # Assuming `move_id` is the account.move (invoice) related to this line
                invoice = record.move_id
                if invoice:
                    # Here you need to correctly reference the sale order. This is a hypothetical solution:
                    # We're assuming that `invoice_origin` holds the name of the sale order.
                    sale_order_name = invoice.invoice_origin

                    if sale_order_name:
                        previous_invoice = self.env['account.move'].search([
                            ('invoice_origin', '=', sale_order_name),
                            ('move_type', '=', 'out_invoice'),
                            ('deductions_no', '=', invoice.deductions_no - 1)
                        ], limit=1)

                        if previous_invoice:
                            previous_invoice_line = self.env['account.move.line'].search([
                                ('move_id', '=', previous_invoice.id),
                                ('product_id', '=', record.product_id.id)
                            ], limit=1)
                            if previous_invoice_line:
                                record.previous_accomplishment = previous_invoice_line.total_accomplishment
                            else:
                                record.previous_accomplishment = 0.0
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
            # if record.previous_accomplishment and record.current_accomplishment:
            record.total_accomplishment = record.previous_accomplishment + record.current_accomplishment
        # else:
        #     record.total_accomplishment = 0.0
