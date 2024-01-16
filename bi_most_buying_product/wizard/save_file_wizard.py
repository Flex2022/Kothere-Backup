# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _

class SaveFileWizard(models.TransientModel):
    _name = "save.file.wizard"
    _description = "Save file Wizard"

    excel_file = fields.Binary('Download Report :- ')
    file_name = fields.Char('Excel File', size=64)