from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    # Invisible Fields
    there_is_access_from_company_id = fields.Boolean(string='There Is Access From Company Id', compute='_compute_there_is_access_from_company_id')

    # Lines Fields
    flex_deductions_ids = fields.One2many('deductions.lines', 'invoice_id', string='Deductions')
    flex_additions_ids = fields.One2many('additions.lines', 'invoice_id', string='Additions')

    # Main Amount Fields
    deductions_amount = fields.Float('Deductions Amount', compute='_compute_deductions_amount', store=True)
    additions_amount = fields.Float('Additions Amount', compute='_compute_additions_amount', store=True)

    # Sub Type Amount Fields
    deductions_amount_type_discounts = fields.Float('Discounts', compute='_compute_deductions_amount', store=True)
    deductions_amount_type_insurances = fields.Float('Insurances', compute='_compute_deductions_amount', store=True)
    deductions_amount_type_advance_payment = fields.Float('Advance Payment', compute='_compute_deductions_amount', store=True)
    deductions_amount_type_business_guarantee = fields.Float('Business Guarantee', compute='_compute_deductions_amount', store=True)

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
            case_1 = self.env['deductions.lines'].search([('invoice_id', '=', record.id), ('deductions_id.type_deductions', '=', '1')])
            record.deductions_amount_type_discounts = sum(case_1.mapped('amount'))
            case_2 = self.env['deductions.lines'].search([('invoice_id', '=', record.id), ('deductions_id.type_deductions', '=', '2')])
            record.deductions_amount_type_insurances = sum(case_2.mapped('amount'))
            case_3 = self.env['deductions.lines'].search([('invoice_id', '=', record.id), ('deductions_id.type_deductions', '=', '3')])
            record.deductions_amount_type_advance_payment = sum(case_3.mapped('amount'))
            case_4 = self.env['deductions.lines'].search([('invoice_id', '=', record.id), ('deductions_id.type_deductions', '=', '4')])
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
                            'line_ids': [
                                (0, 0, {
                                    'name': line.name,
                                    'account_id': record.partner_id.property_account_receivable_id.id,
                                    'debit': line.amount,
                                }),
                                (0, 0, {
                                    'name': line.name,
                                    'account_id': line.deductions_id.account_id.id,
                                    'credit': line.amount,
                                }),
                            ],

                        }).action_post()
                if record.flex_additions_ids:
                    for line in record.flex_additions_ids:
                        journal = self.env['account.move'].create({
                            'ref': line.name,
                            'move_type': 'entry',
                            'line_ids': [(0, 0,{
                                    'name': line.name,
                                    'account_id': line.additions_id.account_id.id,
                                    'debit': line.amount,
                                }),
                                (0, 0, {
                                    'name': line.name,
                                    'account_id': record.partner_id.property_account_receivable_id.id,
                                    'credit': line.amount,
                                }),
                            ],

                        }).action_post()




    def action_post(self):
        res = super(AccountMove, self).action_post()
        if self.there_is_access_from_company_id:

            self.create_journal_entry_when_conferim()
        return res