# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
from odoo.exceptions import UserError
from odoo import api, fields, models, _
from datetime import datetime

class TopProductReport(models.AbstractModel):
    _name = 'report.bi_most_buying_product.top_product_card_report_template'
    _description = "This is  Abstract Model top product report form"

    @api.model
    def _get_report_values(self, docids, data=None):

        docs = self.env['purchase.order'].browse(docids)
        start_date = data['form'].get('start_from_date')
        end_date = data['form'].get('end_to_date')
        selected_option = data['form'].get('select_options')
        limit_numbers = data['form'].get('limit_number')

        purchase_order_line_ids = self.env['purchase.order.line'].search([('order_id.date_approve', '>=', start_date),
                                                                          ('order_id.date_approve', '<=', end_date),
                                                                          ('state', 'in', ['purchase'])], order="product_qty desc")

        product_list = []
        if purchase_order_line_ids:
            if selected_option:
                if selected_option == 'product':
                    for purchase_order_line_id in purchase_order_line_ids:
                        products_id = purchase_order_line_ids.filtered(lambda i: i.product_id.id == purchase_order_line_id.product_id.id)
                        product_value = {}
                        total_quantity = 0
                        product_count_list = []
                        for product in products_id:
                            total_quantity += product.product_qty
                            product_value = {
                                "product_name": product.product_id.name,
                                "product_quantity": total_quantity,
                            }
                        if product_value not in product_list:
                            product_list.append(product_value)
                        if int(limit_numbers):
                            for rec in product_list:
                                if len(product_count_list) < int(limit_numbers):
                                    product_count_list.append(rec)
                        else:
                            product_count_list = product_list.copy()

                if selected_option == 'category':
                    for purchase_order_line_id in purchase_order_line_ids:
                        products_id = purchase_order_line_ids.filtered(lambda i: i.product_id.id == purchase_order_line_id.product_id.id)
                        category_value = {}
                        total_quantity = 0
                        product_count_list = []
                        for product in products_id:
                            total_quantity += product.product_qty
                            category_value = {
                                'product_category': product.product_id.categ_id.name,
                                'product_name': product.product_id.name,
                                'product_quantity': total_quantity,
                                }
                        if category_value not in product_list:
                            product_list.append(category_value)
                        if int(limit_numbers):
                            for rec in product_list:
                                if len(product_count_list) < int(limit_numbers):
                                    product_count_list.append(rec)
                        else:
                            product_count_list = product_list.copy()

                if selected_option == 'price':
                    for purchase_order_line_id in purchase_order_line_ids:
                        products_id = purchase_order_line_ids.filtered(lambda i: i.product_id.id == purchase_order_line_id.product_id.id)
                        product_price_value = {}
                        total_quantity = 0
                        sub_total = 0
                        product_count_list = []
                        for product in products_id:
                            total_quantity += product.product_qty
                            sub_total += product.price_subtotal
                            product_price_value = {
                                'product_name': product.product_id.name,
                                'product_quantity': total_quantity,
                                'product_price': sub_total,
                            }
                        if product_price_value not in product_list:
                            product_list.append(product_price_value)
                        if int(limit_numbers):
                            for rec in product_list:
                                if len(product_count_list) < int(limit_numbers):
                                    product_count_list.append(rec)
                        else:
                            product_count_list = product_list.copy()
            else:
                raise UserError("Please select options.")
        else:
            raise UserError("PRODUCTS IS NOT AVAILABLE !")


        return {
            'docids': docids,
            'data': data,
            'doc_model': 'purchase.order',
            'docs': docs,
            'product_list': sorted(product_count_list, key=lambda var: (-var['product_quantity'])),
            'start_date': data['form'].get('start_from_date'),
            'end_date': data['form'].get('end_to_date'),
        }