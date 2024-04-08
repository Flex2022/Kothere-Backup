# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError
import json
import requests


class BaseModel(models.Model):
    _name = 'hr.notify'
    _description = 'HR Notification'

    name = fields.Char(string='Title', readonly=True)
    body = fields.Text(string='Body', readonly=True)
    date = fields.Datetime(string='Date', readonly=True, default=fields.Datetime.now)
    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee', readonly=True)
    model_name = fields.Char(string='Model', readonly=True)
    res_id = fields.Integer(string='Record Id', readonly=True)
    is_read = fields.Boolean(string='Is Read', readonly=True)
    image_url = fields.Char(string='Image Url', compute='_get_image_url')

    _image_url = {
        "hr.leave": "/hr_holidays/static/description/icon.png",
        "hr.loan": "/nthub_loan_management/static/description/icon.png",
        "hr.expense": "/hr_expense/static/description/icon.png",
    }

    @api.depends('model_name')
    def _get_image_url(self):
        for rec in self:
            rec.image_url = self._image_url.get(rec.model_name, False)
