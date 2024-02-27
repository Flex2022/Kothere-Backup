from odoo import http, _
from odoo.http import request
from odoo.addons.hr_attendance.controllers.main import HrAttendance


class HrAttendanceZktecho(HrAttendance):
    @staticmethod
    def _get_company(token):
        companies = request.env['res.company'].sudo().search([('attendance_kiosk_key', '=', token)], limit=1)
        if companies:
            return companies[0]
        return None
