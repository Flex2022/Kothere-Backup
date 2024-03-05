# -*- coding: utf-8 -*-
from odoo import fields, http, SUPERUSER_ID, _
from odoo.exceptions import ValidationError
from odoo.http import request
import json
import functools
import logging
from datetime import datetime
_logger = logging.getLogger(__name__)
from odoo.tools import groupby
from operator import itemgetter


def validate_token(func):
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        # Get the token from the headers of the requests
        headers = request.httprequest.headers
        token = headers.get('token', '').strip()
        headers_lang = headers.get('lang', 'en').strip()
        lang = 'ar_001' if headers_lang == 'ar' else 'en_US'
        # _logger.info(f"\n\n token    : {token}\n\n")
        # _logger.info(f"\n\n headers  : {headers}\n\n")

        # Check if the token is missing
        if not token:
            res = {"result": {"error": "missing token"}}
            return http.Response(json.dumps(res), status=401, mimetype='application/json')
        
        # Search for the hr_token using the token
        hr_token = request.env["hr.token"].sudo().search([("token", "=", token)], order="id DESC", limit=1)
        
        # Validate the found hr_token
        if not hr_token:
            res = {"result": {"error": "invalid token"}}
            return http.Response(json.dumps(res), status=401, mimetype='application/json')
        
        # Check if the token has expired
        if hr_token.date_expiry < fields.Datetime.now():
            res = {"result": {"error": "expired token"}}
            return http.Response(json.dumps(res), status=401, mimetype='application/json')
        
        # Assuming request.update_context is a method to update the Odoo context,
        # which is not standard, you might intend to do something like this instead:
        # Update the environment context with the employee_id for subsequent operations
        request.env.context = dict(request.env.context, employee_id=hr_token.employee_id.id, lang=lang)
        # request.update_context(employee_id=hr_token.employee_id.id)
        
        # Proceed with the original function
        return func(self, *args, **kwargs)
    return wrap


class HrApi(http.Controller):

    @http.route("/api-hr/login", methods=["GET"], type="http", auth="none", csrf=False)
    def api_hr_login(self, **params):
        headers = request.httprequest.headers
        username = headers.get('username', False)
        password = headers.get('password', False)
        token = headers.get('token', '').strip()
        # _logger.info(f"\n\n headers: {headers}\n\n")
        # _logger.info(f"\n\n token  : {token}\n\n")

        # ====================[Login with token (if expired, update it)]=========================
        show_token_msg = False
        if token:
            hr_token = request.env["hr.token"].sudo().search([("token", "=", token)], order="id DESC", limit=1)
            # if not hr_token:
            #     res = {"result": {"error": "invalid token"}}
            #     return http.Response(json.dumps(res), status=401, mimetype='application/json')
            if hr_token:
                if hr_token.date_expiry < fields.Datetime.now():
                    new_token = hr_token._update_token()
                res = {
                    "result": {
                        "employee_id": hr_token.employee_id.id,
                        "employee_name": hr_token.employee_id.name,
                        "employee_department": {
                            "id": hr_token.employee_id.department_id.id,
                            "name": hr_token.employee_id.department_id.display_name
                        },
                        "employee_job": {
                            "id": hr_token.employee_id.job_id.id,
                            "name": hr_token.employee_id.job_id.name
                        },
                        "employee_work_phone": hr_token.employee_id.work_phone,
                        "employee_work_email": hr_token.employee_id.work_email,
                        "token": hr_token.token,
                    }
                }
                return http.Response(json.dumps(res), status=200, mimetype='application/json')
            else:
                show_token_msg = True
        # =============================================================

        if not (username and password):
            res = {"result": {"error": f"username or password is missing{show_token_msg and ' / invalid token' or ''}"}}
            return http.Response(json.dumps(res), status=400, mimetype='application/json')
        employee = request.env['hr.employee'].sudo().search([('api_username', '=', username)], limit=1)
        if not employee:
            res = {"result": {"error": f"incorrect username{show_token_msg and ' / invalid token' or ''}"}}
            return http.Response(json.dumps(res), status=401, mimetype='application/json')
        if employee.api_password != password:
            res = {"result": {"error": f"incorrect password{show_token_msg and ' / invalid token' or ''}"}}
            return http.Response(json.dumps(res), status=401, mimetype='application/json')
        valid_token = request.env['hr.token'].sudo().get_valid_token(employee_id=employee.id, create=True)
        res = {
            "result": {
                "employee_id": employee.id,
                "employee_name": employee.name,
                "employee_department": {
                    "id": employee.department_id.id,
                    "name": employee.department_id.display_name
                },
                "employee_job": {
                    "id": employee.job_id.id,
                    "name": employee.job_id.name
                },
                "employee_work_phone": employee.work_phone,
                "employee_work_email": employee.work_email,
                "token": valid_token,
            }
        }
        return http.Response(json.dumps(res), status=200, mimetype='application/json')

    @validate_token
    @http.route("/api-hr/update-token", methods=["POST"], type="http", auth="none", csrf=False)
    def api_hr_update_token(self, **post):
        headers = request.httprequest.headers
        token = headers.get('token', '').strip()
        # we are sure that the token is fine because of using the decorator @validate_token
        hr_token = request.env["hr.token"].sudo().search([("token", "=", token)], order="id DESC", limit=1)
        new_token = hr_token._update_token()
        res = {
            "result": {
                "token": new_token,
            }
        }
        return http.Response(json.dumps(res), status=200, mimetype='application/json')

    @validate_token
    @http.route("/api-hr/update-info", methods=["POST"], type="http", auth="none", csrf=False)
    def api_hr_update_info(self, **params):
        employee_id = request.context.get("employee_id")
        if not employee_id:
            res = {"result": {"error": "employee_id is missing in context"}}
            return http.Response(json.dumps(res), status=400, mimetype='application/json')
        employee = request.env['hr.employee'].sudo().browse(employee_id)
        data = json.loads(request.httprequest.data or '{}')
        if data.get('password', False):
            employee.write({'api_password': data['password']})
            res = {"result": {"msg": "Employee data updated successfully"}}
            return http.Response(json.dumps(res), status=200, mimetype='application/json')
        res = {"result": {"msg": "No data to update", }}
        return http.Response(json.dumps(res), status=200, mimetype='application/json')

    @validate_token
    @http.route("/api-hr/my-info", methods=["GET"], type="http", auth="none", csrf=False)
    def api_hr_my_info(self, **params):
        employee_id = request.context.get("employee_id")
        if not employee_id:
            res = {"result": {"error": "employee_id is missing in context"}}
            return http.Response(json.dumps(res), status=400, mimetype='application/json')
        employee = request.env['hr.employee'].sudo().browse(employee_id)
        res = {
            "result": {
                "employee_id": employee.id,
                "employee_name": employee.name,
                "employee_department": {
                    "id": employee.department_id.id,
                    "name": employee.department_id.display_name
                },
                "employee_job": {
                    "id": employee.job_id.id,
                    "name": employee.job_id.name
                },
                "employee_work_phone": employee.work_phone,
                "employee_work_email": employee.work_email,
            }
        }
        return http.Response(json.dumps(res), status=200, mimetype='application/json')

    @validate_token
    @http.route("/api-hr/timeoff-board", methods=["GET"], type="http", auth="none", csrf=False)
    def api_hr_timeoff_board(self, **params):
        employee_id = request.context.get("employee_id")
        if not employee_id:
            res = {"result": {"error": "employee_id is missing in context"}}
            return http.Response(json.dumps(res), status=400, mimetype='application/json')
        employee = request.env['hr.employee'].sudo().browse(employee_id)
        context = {'employee_id': employee_id, 'allowed_company_ids': employee.company_id.ids}
        contextual_leave_type_obj = request.env['hr.leave.type'].sudo().with_context(context)
        allocation_data = contextual_leave_type_obj.get_allocation_data_request()
        data = [{
            "leave_type_name": leave_data[0],
            "leave_type_id": leave_data[3],
            "details": leave_data[1],
            "requires_allocation": leave_data[2],
        } for leave_data in allocation_data]
        res = {"result": data}
        return http.Response(json.dumps(res), status=200, mimetype='application/json')

    @validate_token
    @http.route("/api-hr/create-timeoff", methods=["POST"], type="http", auth="none", csrf=False)
    def api_hr_create_timeoff(self, **params):
        employee_id = request.context.get("employee_id")
        if not employee_id:
            res = {"result": {"error": "employee_id is missing in context"}}
            return http.Response(json.dumps(res), status=400, mimetype='application/json')
        employee = request.env['hr.employee'].sudo().browse(employee_id)
        # data = request.get_json_data()
        payload = json.loads(request.httprequest.data or '{}')
        try:
            leave = request.env['hr.leave'].sudo().with_context(leave_skip_date_check=True).create({
                'employee_id': employee.id,
                'holiday_status_id': payload.get('holiday_status_id'),
                'request_date_from': payload.get('request_date_from'),
                'request_date_to': payload.get('request_date_to'),
            })
            data = {"msg": "timeoff created successfully", "leave_id": leave.id}
            res = {"result": data}
            return http.Response(json.dumps(res), status=200, mimetype='application/json')
        except Exception as ex:
            res = {"result": {"error": f"{ex}"}}
            return http.Response(json.dumps(res), status=401, mimetype='application/json')

    @validate_token
    @http.route("/api-hr/my-timeoff", methods=["GET"], type="http", auth="none", csrf=False)
    def api_hr_my_timeoff(self, **params):
        employee_id = request.context.get("employee_id")
        if not employee_id:
            res = {"result": {"error": "employee_id is missing in context"}}
            return http.Response(json.dumps(res), status=400, mimetype='application/json')
        # employee = request.env['hr.employee'].sudo().browse(employee_id)
        domain = [('employee_id', '=', employee_id), ('state', '=', 'validate')]

        leave_list = request.env['hr.leave'].sudo().search(domain)
        LEAVE = request.env['hr.leave'].sudo()
        leave_by_state = [(state, LEAVE.concat(*leaves)) for state, leaves in groupby(leave_list, itemgetter('state'))]
        data = {}
        # def _selection_name(model, field_name, field_value, lang='en_US'):
        #     names = dict(request.env[model].sudo().with_context(lang='ar_001')._fields[field_name]._description_selection(request.env))
        #     return names.get(field_value, field_value)

        # field_description = lambda model, key: request.env['ir.model.fields'].sudo()._get(model, key)['field_description']
        # all_states = ["draft", "confirm", "refuse", "validate1", "validate"]


        state_info = {
            "draft": _("To Submit"),
            "confirm": _("To Approve"),
            "refuse": _("Refused"),
            "validate1": _("Second Approval"),
            "validate": _("Approved")
        }
        for state, leaves in leave_by_state:
            # print(f"state: {_selection_name('hr.leave', 'state', state, lang='ar_001')}")
            data[state] = {
                "leave_count": len(leaves),
                "description": state_info[state],
                "leaves": [{
                    "employee_id": {
                        "id": leave.employee_id.id,
                        "name": leave.employee_id.name
                    },
                    "holiday_status_id": {
                        "id": leave.holiday_status_id.id,
                        "name": leave.holiday_status_id.name
                    },
                    "number_of_days": leave.number_of_days,
                    "request_date_from": leave.request_date_from.isoformat(),
                    "request_date_to": leave.request_date_to.isoformat(),
                    "date_from": leave.date_from.isoformat(),
                    "date_to": leave.date_to.isoformat(),
                    "state": leave.state,
                } for leave in leaves]
            }
        for state in state_info.keys():
            if state not in data:
                data[state] = {
                    "leave_count": 0,
                    "description": state_info[state],
                    "leaves": []
                }
        res = {"result": data}
        return http.Response(json.dumps(res), status=200, mimetype='application/json')


