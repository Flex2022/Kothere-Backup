# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime

class ExcelReport(models.TransientModel):
	_name="excel.report"
	_description="Excel Report"

	file_name=fields.Binary(string="Excel Report")
	rep_fname=fields.Char(string="File name")