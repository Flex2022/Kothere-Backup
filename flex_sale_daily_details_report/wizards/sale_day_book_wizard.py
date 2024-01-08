from odoo import models, fields, api, _


class FlexSaleBookDayReportWizard(models.TransientModel):
    _name = 'sale.book_day.wizard'
    _description = 'Wizard for Sales Day Book Report'

    date_from = fields.Date(string='Start Date', required=True, default=fields.Date.today())
    date_to = fields.Date(string='End Date', required=True, default=fields.Date.today())
    line_ids = fields.One2many('sale.book_day.wizard.line', 'wizard_id', string='Report Lines')
    payment_ids = fields.One2many('sale.book_day.wizard.payment', 'wizard_id', string='Payments')
    taxes_ids = fields.One2many('sale.book_day.wizard.tax', 'wizard_id', string='Taxes')

    def action_print_pdf(self):
        self.set_line_ids()
        self.set_payment_ids()
        self.set_taxes_ids()
        data = {}
        return self.env.ref('flex_sale_daily_details_report.sale_book_day_report').report_action(self, data=data)

    @api.model
    def _get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('flex_sale_daily_details_report.sale_book_day_report')
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': self,
            'lines': self._lines(),
        }
        return docargs

    def set_line_ids(self):
        # Filter sale order lines based on the specified date range
        sale_order_lines = self.env['sale.order.line'].search([
            ('order_id.date_order', '>=', self.date_from),
            ('order_id.date_order', '<=', self.date_to),
            ('state', '=', 'sale')
        ], order="product_id, price_unit")

        # Fetch and set report lines based on the filtered sale order lines
        report_lines = [(5, 0, 0)]

        # Iterate over distinct product_ids
        for product_id in sale_order_lines.mapped('product_id'):
            product_lines = sale_order_lines.filtered(lambda line: line.product_id == product_id)

            # Iterate over distinct unit prices for the current product
            for unit_price in set(product_lines.mapped('price_unit')):
                product_price_lines = product_lines.filtered(lambda line: line.price_unit == unit_price)

                # Calculate total quantity for the product and unit price combination
                total_quantity = sum(product_price_lines.mapped('product_uom_qty'))

                # Create report line for the product and unit price combination
                report_lines.append((0, 0, {
                    'wizard_id': self.id,
                    'product_id': product_id.id,
                    'quantity': total_quantity,
                    'price_unit': unit_price,
                }))

        self.line_ids = report_lines

    def set_payment_ids(self):
        # Filter payments based on the specified date range and payment type 'inbound'
        payments = self.env['account.payment'].search([
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('state', '=', 'posted'),
            ('payment_type', '=', 'inbound'),
        ])

        # Fetch and set payment lines based on the filtered payments
        payment_lines = [(5, 0, 0)]
        for payment in payments:
            # Create payment line for the payment type
            payment_lines.append((0, 0, {
                'wizard_id': self.id,
                'name': payment.name,
                'amount': payment.amount,
            }))

        self.payment_ids = payment_lines

    def set_taxes_ids(self):
        # Filter sale order lines based on the specified date range and with taxes
        sale_order_lines = self.env['sale.order.line'].search([
            ('order_id.date_order', '>=', self.date_from),
            ('order_id.date_order', '<=', self.date_to),
            ('tax_id', '!=', False),
            ('state', '=', 'sale')
        ])

        tax_lines = [(5, 0, 0)]  # Initialize with the unlink command

        # Iterate over distinct tax_ids
        for tax_id in set(sale_order_lines.mapped('tax_id')):
            tax_lines_info = {
                'wizard_id': self.id,
                'name': tax_id.name,
                'amount': 0.0,
            }

            # Get sale order lines that have this tax
            tax_lines_sale = sale_order_lines.filtered(lambda line: line.tax_id == tax_id)

            for line in tax_lines_sale:
                # Compute the tax amount from the line subtotal
                line_subtotal = line.price_subtotal
                line_tax_amount = line_subtotal * line.tax_id.amount / 100.0
                tax_lines_info['amount'] += line_tax_amount

            tax_lines.append((0, 0, tax_lines_info))

        self.taxes_ids = tax_lines


class FlexSaleBookDayReportWizardLines(models.TransientModel):
    _name = 'sale.book_day.wizard.line'
    _description = 'Wizard for Sales Day Book Report lines'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id,
                                 help='The default company for this user.')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, store=True)
    wizard_id = fields.Many2one('sale.book_day.wizard', string='Wizard Reference', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True,
                                 help='The product related to this line')
    quantity = fields.Float(string='Quantity', required=True,
                            help='The quantity of the product sold on the specified day')
    price_unit = fields.Monetary(string='Unit Price', required=True, help='The unit price of the product')


class FlexSaleBookDayReportWizardPayments(models.TransientModel):
    _name = 'sale.book_day.wizard.payment'
    _description = 'Wizard for Sales Day Book Report payments'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id,
                                 help='The default company for this user.')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, store=True)
    wizard_id = fields.Many2one('sale.book_day.wizard', string='Wizard Reference', required=True, ondelete='cascade')
    name = fields.Char(string='Payment Type', required=True, help='Name')
    amount = fields.Monetary(string='Amount', required=True, help='The total amount of the payment')


class FlexSaleBookDayReportWizardTaxes(models.TransientModel):
    _name = 'sale.book_day.wizard.tax'
    _description = 'Wizard for Sales Day Book Report taxes'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company.id,
                                 help='The default company for this user.')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, store=True)
    wizard_id = fields.Many2one('sale.book_day.wizard', string='Wizard Reference', required=True, ondelete='cascade')
    name = fields.Char(string='Name', required=True, help='Name')
    amount = fields.Monetary(string='Amount', required=True, help='The total amount of the taxes')
