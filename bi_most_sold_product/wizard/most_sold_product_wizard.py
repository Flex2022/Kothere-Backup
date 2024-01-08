# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime
import xlwt
import base64
from io import BytesIO
from odoo.exceptions import UserError, ValidationError

class SoldProductWizard(models.TransientModel):
	_name="sold.product.wizard"
	_description="Sold Product Wizard"

	start_date = fields.Date(string="From", required=True)
	end_date = fields.Date(string="To", required=True)
	limit = fields.Char(string="Most Sold Product Record Limit")
	selection = fields.Selection([
        ('product', 'By Product'),
        ('category', 'By Category'),
        ('sales amount', 'By Sales Amount'),
        ])

	def action_excel_report(self):
		workbook=xlwt.Workbook(encoding='utf-8')
		sheet1=workbook.add_sheet('Report',cell_overwrite_ok=True)
		date_format = xlwt.easyxf({'align:horiz center'})
		date_format.num_format_str='yyyy/mm/dd' 
		format1=xlwt.easyxf('align:horiz center,vert center;font:color black, height 250,bold True')
		format2=xlwt.easyxf('align:horiz left;font:color black, height 210')
		format3=xlwt.easyxf('align:horiz center,vert center;font:color black, height 300,bold True')
		format4=xlwt.easyxf('align:horiz center,vert center;font:color black, height 250,bold True')
		format5=xlwt.easyxf('align:horiz center;font:color black, height 210')

		sheet1.col(0).width = 6000
		sheet1.col(1).width = 6000
		sheet1.col(2).width = 6000
		sheet1.row(1).height = 500
		sheet1.row(3).height = 350
		sheet1.row(6).height = 350
		sheet1.write(3,0,"Start Date",format1)
		sheet1.write(3,1,"End Date",format1)
		sheet1.write(4,0,self.start_date,date_format)
		sheet1.write(4,1,self.end_date,date_format)
		sheet1.write_merge(1,1,0,2, 'Most Sold Products',format3)

		i=8
		sale_order_line_obj = self.env['sale.order.line'].search([('order_id.date_order','>=', self.start_date),('order_id.date_order','<=', self.end_date),('state', 'in', ['sale'])],order="product_uom_qty desc")
		product_list=[]
		if sale_order_line_obj:
			if self.selection:
				if self.selection == 'product':
					sheet1.write(6,0,"Product",format4)
					sheet1.write(6,1,"Qty",format4)
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
						if int(self.limit):
							for record in product_list:
								if len(count_list) < int(self.limit):
									count_list.append(record)
									r=8
									for rec_id in count_list:
										sheet1.write(r,0,rec_id['product_name'],format2)
										sheet1.write(r,1,rec_id['product_qty'],format5)
										r+=1
						else:
							count_list = product_list.copy()
							r=8
							for rec_id in count_list:
								sheet1.write(r,0,rec_id['product_name'],format2)
								sheet1.write(r,1,rec_id['product_qty'],format5)
								r+=1

				if self.selection == 'category':
					sheet1.write(6,0,"Product Category",format4)
					sheet1.write(6,1,"Product",format4)
					sheet1.write(6,2,"Qty",format4)
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
					    if int(self.limit):
					    	for record in product_list:
					    		if len(count_list) < int(self.limit):
					    			count_list.append(record)
					    			r=8
					    			for rec_id in count_list:
					    				sheet1.write(r,0,rec_id['product_category'],format2)
					    				sheet1.write(r,1,rec_id['product_name'],format2)
					    				sheet1.write(r,2,rec_id['product_qty'],format5)
					    				r+=1
					    else:
					    	count_list = product_list.copy()
					    	r=8
					    	for rec_id in count_list:
					    		sheet1.write(r,0,rec_id['product_category'],format2)
					    		sheet1.write(r,1,rec_id['product_name'],format2)
					    		sheet1.write(r,2,rec_id['product_qty'],format5)
					    		r+=1

				if self.selection == 'sales amount':
				    sheet1.write(6,0,"Product",format4)
				    sheet1.write(6,1,"Qty",format4)
				    sheet1.write(6,2,"Total Price",format4)
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
				        if int(self.limit):
				        	for record in product_list:
				        		if len(count_list) < int(self.limit):
				        			count_list.append(record)
				        			r=8
				        			for rec_id in count_list:
				        				sheet1.write(r,0,rec_id['product_name'],format2)
				        				sheet1.write(r,1,rec_id['product_qty'],format5)
				        				sheet1.write(r,2,rec_id['product_price_subtotal'],format5)
				        				r+=1
				        else:
				        	count_list = product_list.copy()
				        	r=8
				        	for rec_id in count_list:
				        		sheet1.write(r,0,rec_id['product_name'],format2)
				        		sheet1.write(r,1,rec_id['product_qty'],format5)
				        		sheet1.write(r,2,rec_id['product_price_subtotal'],format5)
				        		r+=1
			else:
				raise UserError("Please Select Any Selection")
		else:
			raise UserError("No record found for this time duration")

		filename=self.selection + ' excel report ' + '.xls'
		stream=BytesIO()
		workbook.save(stream)
		out=base64.encodebytes(stream.getvalue())
		excel_id=self.env['excel.report'].create({
												"rep_fname":filename,
												"file_name":out,
												})
		stream.close()
		return{
			'res_id':excel_id.id,
			'name':'Print Excel Report',
			'view_type':'form',
			'view_mode':'form',
			'res_model':'excel.report',
			'type':'ir.actions.act_window',
			'target':'new',
			}

	def action_pdf_report(self):
		datas = {
				'form_data':self.read()[0],
				}
		return self.env.ref('bi_most_sold_product.action_most_sold_product_report').report_action(self, data=datas)