# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


def notification(self, user_id, date, activity_type, model, note, warning):
    if user_id:
        notification = {
            'activity_type_id': self.env.ref(activity_type).id,
            'res_id': self.id,
            'res_model_id': self.env['ir.model'].search([('model', '=', model)], limit=1).id,
            'icon': 'fa-pencil-square-o',
            'date_deadline': date,
            'user_id': user_id.id,
            'note': note
        }
        self.env['mail.activity'].create(notification)
    else:
        raise ValidationError(warning)


def send_email(self, email_to, auther, subject,  mail_content, warning):
    if email_to:
        main_content = {
            'subject': subject,
            'author_id': auther,
            'body_html': mail_content,
            'email_to': email_to,
        }
        self.env['mail.mail'].sudo().create(main_content).send()
    else:
        raise ValidationError(warning)
