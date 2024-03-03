# -*- coding: utf-8 -*-
from odoo import fields, http, SUPERUSER_ID
from odoo.http import request
import json
import functools
import logging
from datetime import datetime
_logger = logging.getLogger(__name__)


def validate_token(func):
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        # Access the access_token from the query parameters for GET requests
        access_token = request.httprequest.args.get('access_token', '').strip()
        
        # Check if the access_token is missing
        if not access_token:
            res = {"result": {"error": "missing access token"}}
            return http.Response(json.dumps(res), status=401, mimetype='application/json')
        
        # Search for the hr_token using the access_token
        hr_token = request.env["hr.token"].sudo().search([("token", "=", access_token)], order="id DESC", limit=1)
        
        # Validate the found hr_token
        if not hr_token:
            res = {"result": {"error": "invalid access token"}}
            return http.Response(json.dumps(res), status=401, mimetype='application/json')
        
        # Check if the token has expired
        if hr_token.date_expiry < datetime.now():
            res = {"result": {"error": "expired access token"}}
            return http.Response(json.dumps(res), status=401, mimetype='application/json')
        
        # Assuming request.update_context is a method to update the Odoo context,
        # which is not standard, you might intend to do something like this instead:
        # Update the environment context with the employee_id for subsequent operations
        request.env.context = dict(request.env.context, employee_id=hr_token.employee_id.id)
        
        # Proceed with the original function
        return func(self, *args, **kwargs)
    return wrap


class HrApi(http.Controller):

    @http.route("/api-hr/login", methods=["GET"], type="http", auth="none", csrf=False)
    def api_hr_login(self, **params):
        headers = request.httprequest.headers
        username = headers.get('username', False)
        password = headers.get('password', False)

        # ====================[Login with access token (if expired, update it)]=========================
        access_token = request.httprequest.headers.get('access_token')
        if access_token:
            hr_token = request.env["hr.token"].sudo().search([("token", "=", access_token)], order="id DESC", limit=1)
            if not hr_token:
                res = {"result": {"error": "invalid access token"}}
                return http.Response(json.dumps(res), status=401, mimetype='application/json')
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
                    "access_token": hr_token.token,
                }
            }
            return http.Response(json.dumps(res), status=200, mimetype='application/json')
        # =============================================================

        if not (username and password):
            res = {"result": {"error": "username or password is missing"}}
            return http.Response(json.dumps(res), status=400, mimetype='application/json')
        employee = request.env['hr.employee'].sudo().search([('api_username', '=', username)], limit=1)
        if not employee:
            res = {"result": {"error": "incorrect username"}}
            return http.Response(json.dumps(res), status=401, mimetype='application/json')
        if employee.api_password != password:
            res = {"result": {"error": "incorrect password"}}
            return http.Response(json.dumps(res), status=401, mimetype='application/json')
        access_token = request.env['hr.token'].sudo().get_valid_token(employee_id=employee.id, create=True)
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
                "access_token": access_token,
            }
        }
        return http.Response(json.dumps(res), status=200, mimetype='application/json')

    @validate_token
    @http.route("/api-hr/update-token", methods=["POST"], type="http", auth="none", csrf=False)
    def api_hr_update_token(self, **post):
        access_token = request.httprequest.headers.get('access_token')
        # we are sure that the token is fine because of using the decorator @validate_token
        hr_token = request.env["hr.token"].sudo().search([("token", "=", access_token)], order="id DESC", limit=1)
        new_token = hr_token._update_token()
        res = {
            "result": {
                "access_token": new_token,
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
    @http.route("/api-hr/timeoff-board", methods=["GET"], type="http", auth="none", csrf=False)
    def api_hr_timeoff_board(self, **params):
        employee_id = request.context.get("employee_id")
        if not employee_id:
            res = {"result": {"error": "employee_id is missing in context"}}
            return http.Response(json.dumps(res), status=400, mimetype='application/json')
        employee = request.env['hr.employee'].sudo().browse(employee_id)
        context = {'employee_id': employee_id, 'allowed_company_ids': employee.company_id.ids}
        contextual_leave_type_obj = request.env['hr.leave.type'].sudo().with_context(context)
        data = contextual_leave_type_obj.get_allocation_data_request()
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
        leave = request.env['hr.leave'].sudo().create({
            'employee_id': employee.id,
            'holiday_status_id': payload.get('holiday_status_id'),
            'request_date_from': payload.get('request_date_from'),
            'request_date_to': payload.get('request_date_to'),
        })
        data = {"msg": "timeoff created successfully", "leave_id": leave.id}
        res = {"result": data}
        return http.Response(json.dumps(res), status=200, mimetype='application/json')

