# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
import base64
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
import io
import xlwt

class TopProductWizard(models.TransientModel):
    _name = "top.product.wizard"
    _description = "Top Product Wizard"

    start_from_date = fields.Date("From Date")
    end_to_date = fields.Date("To Date")
    limit_number = fields.Char("Limit")
    select_options = fields.Selection([('product', 'For Product'),
                                         ('category', 'For Category '),
                                         ('price', 'Purchased Price '), ], string="Select Options")

    @api.constrains('start_from_date', 'end_to_date')
    def _check_dates(self):
        for record in self:
            if record.start_from_date and record.end_to_date:
                if record.end_to_date < record.start_from_date:
                    raise ValidationError("End date must be greater than start date!")

    def button_create_pdf_wizard(self):
        data = {
        'model': 'top.product.wizard',
        'form': self.read()[0],
        }
        return self.env.ref('bi_most_buying_product.action_top_product_report_template').report_action(self, data=data)

    def button_create_excel_wizard(self):
        filename = 'Top Product Report' + '.xls'
        date_formate = xlwt.XFStyle()
        date_formate.num_format_str = "YY-mm-DD"
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('Most Buying Product', cell_overwrite_ok=True)
        style_formate1 = xlwt.easyxf()
        style_formate2 = xlwt.easyxf('align:horiz center,vert center;font:color black, height 250,bold True')
        style_formate3 = xlwt.easyxf("align:horiz center,vert center")
        GREEN_TABLE_HEADER = xlwt.easyxf(
            'font: bold 1, name Tahoma, height 350;'
            'align: vertical center, horizontal center, wrap on;'
            'borders: top thick, bottom thick, left thick, right thick;'
        )

        worksheet.col(0).width = 6000
        worksheet.col(1).width = 6000
        worksheet.col(2).width = 6000
        worksheet.col(3).width = 6000
        worksheet.col(4).width = 6000
        worksheet.write(5, 0, "FROM DATE", style_formate2)
        worksheet.write(6, 0, "TO DATE", style_formate2)
        worksheet.write_merge(
            0, 2, 0, 2, 'Most Buying Product', GREEN_TABLE_HEADER)
        worksheet.write(5, 1, self.start_from_date, date_formate)
        worksheet.write(6, 1, self.end_to_date, date_formate)

        purchase_order_line_ids = self.env['purchase.order.line'].search([('order_id.date_approve', '>=', self.start_from_date),
                                                                          ('order_id.date_approve', '<=', self.end_to_date),
                                                                          ('state', 'in', ['purchase'])], order="product_qty desc")

        product_list = []
        if purchase_order_line_ids:
            if self.select_options:
                if self.select_options == 'product':
                    worksheet.write(10, 0, "PRODUCTS", style_formate2)
                    worksheet.write(10, 1, "QUANTITY", style_formate2)
                    for purchase_order_line_id in purchase_order_line_ids:
                        products_id = purchase_order_line_ids.filtered(lambda var: var.product_id.id == purchase_order_line_id.product_id.id)
                        product_value = {}
                        total_quantity = 0
                        product_count_list = []
                        for product in products_id:
                            total_quantity += product.product_qty
                            product_value.update({
                                'product_name': product.product_id.name,
                                'product_quantity': total_quantity,
                            })
                        if product_value not in product_list:
                            product_list.append(product_value)
                        if int(self.limit_number):
                            for rec in product_list:
                                if len(product_count_list) < int(self.limit_number):
                                    product_count_list.append(rec)
                                    product_sort_list = sorted(product_count_list, key=lambda var: (-var['product_quantity'], var['product_name']))
                                    row = 11
                                    for product_count in product_sort_list:
                                        worksheet.write(row, 0, product_count['product_name'], style_formate1)
                                        worksheet.write(row, 1, product_count['product_quantity'], style_formate3)
                                        row += 1
                        else:
                            product_count_list = product_list.copy()
                            product_sort_list = sorted(product_count_list,
                                                       key=lambda var: (-var['product_quantity'], var['product_name']))

                            row = 11
                            for product_count in product_sort_list:
                                worksheet.write(row, 0, product_count['product_name'], style_formate1)
                                worksheet.write(row, 1, product_count['product_quantity'], style_formate3)
                                row += 1

                if self.select_options == 'category':
                    worksheet.write(10, 0, "CATEGORY", style_formate2)
                    worksheet.write(10, 1, "PRODUCTS", style_formate2)
                    worksheet.write(10, 2, "QUANTITY", style_formate2)
                    for purchase_order_line_id in purchase_order_line_ids:
                        products_id = purchase_order_line_ids.filtered(lambda var: var.product_id.id == purchase_order_line_id.product_id.id)
                        product_value = {}
                        total_quantity = 0
                        product_count_list = []
                        for product in products_id:
                            total_quantity += product.product_qty
                            product_value = {
                                'product_category': product.product_id.categ_id.name,
                                'product_name': product.product_id.name,
                                'product_quantity': total_quantity,
                            }
                        if product_value not in product_list:
                            product_list.append(product_value)
                        if int(self.limit_number):
                            for rec in product_list:
                                if len(product_count_list) < int(self.limit_number):
                                    product_count_list.append(rec)
                                    product_sort_list = sorted(product_count_list, key=lambda var: (-var['product_quantity'], var['product_name']))

                                    row = 11
                                    for product_count in product_sort_list:
                                        worksheet.write(row, 0, product_count['product_category'], style_formate1)
                                        worksheet.write(row, 1, product_count['product_name'], style_formate1)
                                        worksheet.write(row, 2, product_count['product_quantity'], style_formate3)
                                        row += 1
                        else:
                            product_count_list = product_list.copy()
                            product_sort_list = sorted(product_count_list,
                                                       key=lambda var: (-var['product_quantity'], var['product_name']))

                            row = 11
                            for product_count in product_sort_list:
                                worksheet.write(row, 0, product_count['product_category'], style_formate1)
                                worksheet.write(row, 1, product_count['product_name'], style_formate1)
                                worksheet.write(row, 2, product_count['product_quantity'], style_formate3)
                                row += 1

                if self.select_options == 'price':
                    worksheet.write(10, 0, "PRODUCTS", style_formate2)
                    worksheet.write(10, 1, "QUANTITY", style_formate2)
                    worksheet.write(10, 2, "TOTAL PRICE", style_formate2)

                    for purchase_order_line_id in purchase_order_line_ids:
                        products_id = purchase_order_line_ids.filtered(lambda var: var.product_id.id == purchase_order_line_id.product_id.id)
                        product_value = {}
                        total_quantity = 0
                        sub_total = 0
                        product_count_list = []
                        for product in products_id:
                            total_quantity += product.product_qty
                            sub_total += product.price_subtotal
                            product_value = {
                                'product_name': product.product_id.name,
                                'product_quantity': total_quantity,
                                "product_price": sub_total,
                            }
                        if product_value not in product_list:
                            product_list.append(product_value)
                        if int(self.limit_number):
                            for rec in product_list:
                                if len(product_count_list) < int(self.limit_number):
                                    product_count_list.append(rec)
                                    product_sort_list = sorted(product_count_list, key=lambda var: (-var['product_quantity'], var['product_name']))

                                    row = 11
                                    for product_count in product_sort_list:
                                        worksheet.write(row, 0, product_count['product_name'], style_formate1)
                                        worksheet.write(row, 1, product_count['product_quantity'], style_formate3)
                                        worksheet.write(row, 2, product_count['product_price'], style_formate3)
                                        row += 1
                        else:
                            product_count_list = product_list.copy()
                            product_sort_list = sorted(product_count_list,
                                                       key=lambda var: (-var['product_quantity'], var['product_name']))

                            row = 11
                            for product_count in product_sort_list:
                                worksheet.write(row, 0, product_count['product_name'], style_formate1)
                                worksheet.write(row, 1, product_count['product_quantity'], style_formate3)
                                worksheet.write(row, 2, product_count['product_price'], style_formate3)
                                row += 1

            else:
                raise UserError("Please select options")
        else:
            raise UserError("PRODUCTS IS NOT AVAILABLE !")

        stream = io.BytesIO()
        workbook.save(stream)
        out = base64.encodebytes(stream.getvalue())
        excel_id = self.env['save.file.wizard'].create({"file_name": filename,
                                                          "excel_file": out})
        return {

            'res_id': excel_id.id,
            'name': 'Excel report',
            'view_mode': 'form',
            'res_model': 'save.file.wizard',
            'view_id': False,
            'target': 'new',
            'type': 'ir.actions.act_window'

        }



