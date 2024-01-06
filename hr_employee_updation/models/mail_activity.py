# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    @api.onchange('activity_type_id')
    def _onchange_activity_type_id(self):
        if self.activity_type_id:
            self.summary = self.activity_type_id.summary
            base = fields.Date.context_today(self)
            if self.activity_type_id.delay_from == 'previous_activity' and 'activity_previous_deadline' in self.env.context:
                base = fields.Date.from_string(self.env.context.get('activity_previous_deadline'))
            self.date_deadline = base + relativedelta(**{self.activity_type_id.delay_unit: self.activity_type_id.delay_count})
            self.note = self.activity_type_id.default_description
