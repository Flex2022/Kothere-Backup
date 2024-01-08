# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime, timedelta
from dateutil import parser
import time
from odoo.exceptions import UserError, ValidationError

class SaleSoldProductReport(models.AbstractModel):
    _name = 'report.bi_most_sold_product.most_sold_product_report_template'
    _description = 'Sale Sold Product Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['sale.order'].browse(docids)
        date_start = data['form_data'].get('start_date')
        date_end = data['form_data'].get('end_date')
        record_limit = data['form_data'].get('limit')
        selection_value = data['form_data'].get('selection')
        
        sale_order_line_obj = self.env['sale.order.line'].search([('order_id.date_order','>=', date_start),('order_id.date_order','<=', date_end),('state', 'in', ['sale'])])
        product_list=[]
        if sale_order_line_obj:
            if selection_value:
                if selection_value == 'product':
                    for rec in sale_order_line_obj:
                        products = sale_order_line_obj.filtered(lambda i: i.product_id.id == rec.product_id.id)
                        dict_value = {}
                        quantity = 0
                        count_list = []
                        for line in products:
                            quantity += line.product_uom_qty
                            dict_value.update({
                                'product_name':line.product_id.name,
                                'product_qty':quantity,
                                })
                        if dict_value not in product_list:
                            product_list.append(dict_value)
                        if int(record_limit):
                            for record in product_list:
                                if len(count_list) < int(record_limit):
                                    count_list.append(record)
                        else:
                            count_list = product_list.copy()
                
                if selection_value == 'category':
                    for rec in sale_order_line_obj:
                        products = sale_order_line_obj.filtered(lambda i: i.product_id.id == rec.product_id.id)
                        dict_value = {}
                        quantity = 0
                        count_list = []
                        for line in products:
                            quantity += line.product_uom_qty
                            dict_value.update({
                                'product_category':line.product_id.categ_id.name,
                                'product_name':line.product_id.name,
                                'product_qty':quantity,
                                })
                        if dict_value not in product_list:
                            product_list.append(dict_value)
                        if int(record_limit):
                            for record in product_list:
                                if len(count_list) < int(record_limit):
                                    count_list.append(record)
                        else:
                            count_list = product_list.copy()

                if selection_value == 'sales amount':
                    for rec in sale_order_line_obj:
                        products = sale_order_line_obj.filtered(lambda i: i.product_id.id == rec.product_id.id)
                        dict_value = {}
                        quantity = 0
                        subtotal = 0
                        count_list = []
                        for line in products:
                            quantity += line.product_uom_qty
                            subtotal += line.price_subtotal
                            dict_value.update({
                                'product_name':line.product_id.name,
                                'product_qty':quantity,
                                'product_price_subtotal':subtotal,
                                })
                        if dict_value not in product_list:
                            product_list.append(dict_value)
                        if int(record_limit):
                            for record in product_list:
                                if len(count_list) < int(record_limit):
                                    count_list.append(record)
                        else:
                            count_list = product_list.copy()
            
            else:
                raise UserError("Please Select Any Selection")
        else:
            raise UserError("No record found for this time duration")


        return {
            'docids': docids,
            'doc_model': 'sale.order',
            'docs': docs,
            'data': data,
            'product_list':sorted(count_list, key=lambda i: (-i['product_qty'])),
            }