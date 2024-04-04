import base64
import io

from odoo import fields, models, api, _
from odoo.exceptions import UserError
import tempfile
import binascii
import xlrd
import pandas as pd
from io import BytesIO


class EstimateOrder(models.Model):
    _inherit = 'job.estimate'

    excel_file = fields.Binary(string='Excel File', attachment=True)

    def read_excel_file(self):
        if not self.excel_file:
            raise UserError(_('Please upload an excel file'))
        file = io.BytesIO(base64.b64decode(self.excel_file))
        data = pd.read_excel(file, engine='openpyxl')
        if not self._check_if_the_excel_is_depended_on_my_template(data):
            raise UserError(_('Please use the right template'))
        Material = data[data['Type'].isin(['Material'])]
        Processing = data[data['Type'].isin(['Processing'])]
        Misc = data[data['Type'].isin(['Misc Items'])]
        Other = data[data['Type'].isin(['Other'])]
        if not self._check_empty_lines(Other):
            self._create_other_lines(Other)
        if not self._check_empty_lines(Material):
            self._create_material_lines(Material)
        if not self._check_empty_lines(Processing):
            self._create_Processing_lines(Processing)
        if not self._check_empty_lines(Misc):
            self._create_Misc_lines(Misc)
        self.excel_file = False

    def _check_empty_lines(self, df):
        return df.empty

    def _create_other_lines(self, df):
        for index, row in df.iterrows():

            pruduct = self.env['product.product'].search([('name', '=', row['Profile'])]).id
            if not pruduct:
                self.env['product.product'].create({
                    'name': row['Profile'],
                    'type': 'product',
                })
            self.env['other.estimate'].create({
                'other_id': self.id,
                'product_id': self.env['product.product'].search([('name', '=', row['Profile'])]).id,
                'quantity': row['Qty.'],
                # 'cost': row['Unit Price'],
                # 'product_uom': self.env['uom.uom'].search([('name', '=', row['UOM'])]).id,
                'cost': row['Unit Price'],
                # 'subtotal': row['Total Price'],
                # 'type': row['Type'],
            })

    def _create_material_lines(self, df):
        for index, row in df.iterrows():
            pruduct = self.env['product.product'].search([('name', '=', row['Profile'])]).id
            if not pruduct:
                self.env['product.product'].create({
                    'name': row['Profile'],
                    'type': 'product',

                })
            self.env['material.estimate'].create({
                'material_id': self.id,
                'product_id': self.env['product.product'].search([('name', '=', row['Profile'])]).id,
                'quantity': row['Qty.'],
                # 'product_uom': self.env['uom.uom'].search([('name', '=', row['UOM'])]).id,
                'cost': row['Unit Price'],
                # 'subtotal': row['Total Price'],
                # 'type': row['Type'],
            })

    def _create_Misc_lines(self, df):
        for index, row in df.iterrows():
            pruduct = self.env['product.product'].search([('name', '=', row['Profile'])]).id
            if not pruduct:
                self.env['product.product'].create({
                    'name': row['Profile'],
                    'type': 'product',
                })
            self.env['overhead.estimate'].create({
                'overhead_id': self.id,
                'product_id': self.env['product.product'].search([('name', '=', row['Profile'])]).id,
                'quantity': row['Qty.'],
                # 'product_uom': self.env['uom.uom'].search([('name', '=', row['UOM'])]).id,
                'cost': row['Unit Price'],
                # 'subtotal': row['Total Price'],
                # 'type': row['Type'],
            })

    def _create_Processing_lines(self, df):
        for index, row in df.iterrows():
            pruduct = self.env['product.product'].search([('name', '=', row['Profile'])]).id
            if not pruduct:
                self.env['product.product'].create({
                    'name': row['Profile'],
                    'type': 'product',
                })
            self.env['labour.estimate'].create({
                'labour_id': self.id,
                'product_id': self.env['product.product'].search([('name', '=', row['Profile'])]).id,
                'quantity': row['Qty.'],
                # 'product_uom': self.env['uom.uom'].search([('name', '=', row['UOM'])]).id,
                'cost': row['Unit Price'],
                # 'subtotal': row['Total Price'],
                # 'type': row['Type'],
            })

    def _check_if_the_excel_is_depended_on_my_template(self, df):
        return df.columns.tolist() == ['Type', 'Profile', 'Qty.', 'Unit', 'Grade', 'Unit Weight', 'Total Weight',
                                       'Price/kg', 'Unit Price', 'Total Price', 'Percentage %']
