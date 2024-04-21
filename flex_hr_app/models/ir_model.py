# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError
import json
import requests


# class BaseModel(models.Model):
class BaseModel(models.AbstractModel):

    # _inherit = 'ir.model'
    _inherit = 'base'

    def get_hr_app_models(self):
        return [
            'hr.leave',
            'hr.loan',
            'hr.expense',
            'flex.approval.resignation',
            'flex.approval.renew_iqama',
            'flex.approval.business_trip',
        ]

    def write(self, vals):
        if (('state' not in vals)
                or (self._name not in self.get_hr_app_models())
                or (any(fname not in self._fields for fname in ['employee_id', 'state']))):
            return super(BaseModel, self).write(vals)
        res = super(BaseModel, self).write(vals)
        for record in self:
            title = self._description
            body = '%s set to %s' % (record.display_name, record.state)
            record.employee_id.send_app_notification(title, body, model_name=record._name, res_id=record.id)
        return res
