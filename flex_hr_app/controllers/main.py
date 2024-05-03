# -*- coding: utf-8 -*-
from odoo import fields, http, SUPERUSER_ID, _
from odoo.exceptions import ValidationError
from odoo.http import request
import json
import functools
import base64
import logging
from datetime import datetime
_logger = logging.getLogger(__name__)
from odoo.tools import groupby
from operator import itemgetter
import werkzeug.exceptions
from odoo.tools import html2plaintext


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
            # 403: forbidden
            return http.Response(json.dumps(res), status=403, mimetype='application/json')

        # Search for the hr_token using the token
        hr_token = request.env["hr.token"].sudo().search([("token", "=", token)], order="id DESC", limit=1)

        # Validate the found hr_token
        if not hr_token:
            res = {"result": {"error": "invalid token"}}
            return http.Response(json.dumps(res), status=403, mimetype='application/json')

        # Check if the token has expired
        if hr_token.date_expiry < fields.Datetime.now():
            res = {"result": {"error": "expired token"}}
            return http.Response(json.dumps(res), status=403, mimetype='application/json')

        # Assuming request.update_context is a method to update the Odoo context,
        # which is not standard, you might intend to do something like this instead:
        # Update the environment context with the employee_id for subsequent operations
        request.env.context = dict(request.env.context, employee_id=hr_token.employee_id.id, lang=lang)
        # request.update_context(employee_id=hr_token.employee_id.id)

        # Proceed with the original function
        return func(self, *args, **kwargs)
    return wrap


class HrApi(http.Controller):

    def _get_field_selections(self, model_name, field_name):
        field = request.env['ir.model.fields'].sudo().search([('model', '=', model_name), ('name', '=', field_name)])
        return {sel.value: sel.name for sel in field.selection_ids}

    @http.route("/api-hr/login", methods=["GET"], type="http", auth="none", csrf=False)
    def api_hr_login(self, **params):
        headers = request.httprequest.headers
        # username = headers.get('username', False)
        # password = headers.get('password', False)
        # token = headers.get('token', '').strip()
        device_token = headers.get('deviceToken', '').strip()
        # print(f"headers: {headers}")
        _logger.info(f"\nheaders: {headers}")
        _logger.info(f"\ndevice_token: {device_token}")
        auth_header = headers.get('Authorization')
        if not auth_header.startswith('Basic '):
            res = {"result": {"error": f"Authorization type should be 'Basic Auth'"}}
            return http.Response(json.dumps(res), status=406, mimetype='application/json')
        # Get the base64 encoded string after 'Basic '
        encoded_credentials = auth_header[len('Basic '):]
        # Decode the base64 string
        credentials = base64.b64decode(encoded_credentials).decode('utf-8')
        # Split the credentials into username and password
        username, password = credentials.split(':', 1)
        # print('username: ', username)
        # print('password: ', password)
        if not (username and password):
            res = {"result": {"error": f"username or password is missing"}}
            return http.Response(json.dumps(res), status=406, mimetype='application/json')
        employee = request.env['hr.employee'].sudo().search([('api_username', '=', username)], limit=1)
        if not employee:
            res = {"result": {"error": f"incorrect username"}}
            return http.Response(json.dumps(res), status=406, mimetype='application/json')
        if employee.api_password != password:
            res = {"result": {"error": f"incorrect password"}}
            return http.Response(json.dumps(res), status=406, mimetype='application/json')
        valid_token = request.env['hr.token'].sudo().get_valid_token(employee_id=employee.id, device_token=device_token, create=True)
        contract = employee.contract_id
        salary = contract.wage
        allowance_fields = ['call_allowance', 'food_allowance', 'position_allowance']
        # deduction_fields = []
        for field_name in allowance_fields:
            if field_name in contract:
                salary += contract[field_name]
        # for field_name in deduction_fields:
        #     if field_name in contract:
        #         salary -= contract[field_name]
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
                "image_url": f"/web/force/image/hr.employee.public/{employee.id}/image_1920",
                # =================================
                "identification_id": employee.identification_id,
                "children": employee.children,
                "contract_id": employee.contract_id.id,
                "contract_name": employee.contract_id.name,
                "contract_type": employee.contract_id.contract_type_id.name,
                "working_schedule": employee.contract_id.hours_per_week,
                "contract_start_date": employee.first_contract_date and employee.first_contract_date.isoformat(),
                "salary_type": employee.contract_id.wage_type,
                # "basic_salary": employee.contract_id._get_contract_wage(),
                "basic_salary": salary,
                # =================================
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
        contract = employee.contract_id
        salary = contract.wage
        allowance_fields = ['call_allowance', 'food_allowance', 'position_allowance']
        # deduction_fields = []
        for field_name in allowance_fields:
            if field_name in contract:
                salary += contract[field_name]
        # for field_name in deduction_fields:
        #     if field_name in contract:
        #         salary -= contract[field_name]
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
                # =================================
                "identification_id": employee.identification_id,
                "children": employee.children,
                "contract_id": employee.contract_id.id,
                "contract_name": employee.contract_id.name,
                "contract_type": employee.contract_id.contract_type_id.name,
                "working_schedule": employee.contract_id.hours_per_week,
                "contract_start_date": employee.first_contract_date and employee.first_contract_date.isoformat(),
                "salary_type": employee.contract_id.wage_type,
                # "basic_salary": employee.contract_id._get_contract_wage(),
                "basic_salary": salary,
                # =================================
                "image_url": f"/web/force/image/hr.employee.public/{employee.id}/image_1920",
            }
        }
        return http.Response(json.dumps(res), status=200, mimetype='application/json')

    @validate_token
    @http.route('/api-hr/my-notification', type='http', auth='none', methods=['GET'], csrf=False)
    def api_hr_my_notification(self, **params):
        employee_id = request.context.get("employee_id")
        if not employee_id:
            res = {"result": {"error": "employee_id is missing in context"}}
            return http.Response(json.dumps(res), status=400, mimetype='application/json')
        data = []
        notifications = request.env['hr.notify'].sudo().search([('employee_id', '=', employee_id)], order="id desc")
        for notify in notifications:
            data.append({
                "id": notify.id,
                "name": notify.name,
                "body": notify.body,
                "date": notify.date.isoformat(),
                "model_name": notify.model_name,
                "res_id": notify.res_id,
                "is_read": notify.is_read,
                "image_url": notify.image_url,
            })
            notify.is_read = True
        res = {
            "result": {"data": data},
        }
        return http.Response(
            json.dumps(res),
            status=200,
            mimetype='application/json'
        )

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
                'name': payload.get('name'),
            })
            base64_str = payload.get('document')
            if base64_str:
                request.env['ir.attachment'].sudo().create({
                    'name': 'Document',
                    'datas': base64_str,
                    'res_model': 'hr.leave',
                    'res_id': leave.id,
                    'type': 'binary',
                })
            data = {"msg": "timeoff created successfully", "leave_id": leave.id}
            res = {"result": data}
            return http.Response(json.dumps(res), status=200, mimetype='application/json')
        except Exception as ex:
            res = {"result": {"error": f"{ex}"}}
            # 406: not acceptable
            return http.Response(json.dumps(res), status=406, mimetype='application/json')

    @validate_token
    @http.route("/api-hr/my-timeoff", methods=["GET"], type="http", auth="none", csrf=False)
    def api_hr_my_timeoff(self, **params):
        employee_id = request.context.get("employee_id")
        if not employee_id:
            res = {"result": {"error": "employee_id is missing in context"}}
            return http.Response(json.dumps(res), status=400, mimetype='application/json')
        # employee = request.env['hr.employee'].sudo().browse(employee_id)
        domain = [('employee_id', '=', employee_id)]

        leave_list = request.env['hr.leave'].sudo().search(domain)
        LEAVE = request.env['hr.leave'].sudo()
        leave_by_state = [(state, LEAVE.concat(*leaves)) for state, leaves in groupby(leave_list, itemgetter('state'))]
        data = {}
        # def _selection_name(model, field_name, field_value, lang='en_US'):
        #     names = dict(request.env[model].sudo().with_context(lang='ar_001')._fields[field_name]._description_selection(request.env))
        #     return names.get(field_value, field_value)

        # field_description = lambda model, key: request.env['ir.model.fields'].sudo()._get(model, key)['field_description']
        # all_states = ["draft", "confirm", "refuse", "validate1", "validate"]

        # state_info = {
        #     "draft": _("To Submit"),
        #     "confirm": _("To Approve"),
        #     "refuse": _("Refused"),
        #     "validate1": _("Second Approval"),
        #     "validate": _("Approved")
        # }
        state_info = self._get_field_selections('hr.leave', 'state')
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

    @validate_token
    @http.route("/api-hr/my-payslip", methods=["GET"], type="http", auth="none", csrf=False)
    def api_hr_my_payslip(self, **params):
        employee_id = request.context.get("employee_id")
        if not employee_id:
            res = {"result": {"error": "employee_id is missing in context"}}
            return http.Response(json.dumps(res), status=400, mimetype='application/json')
        if request.env['ir.module.module'].sudo().search([('name', '=', 'hr_payroll')], limit=1).state != 'installed':
            res = {"result": {"error": "payroll app not installed"}}
            return http.Response(json.dumps(res), status=400, mimetype='application/json')
        # employee = request.env['hr.employee'].sudo().browse(employee_id)
        domain = [('employee_id', '=', employee_id), ('state', 'in', ['done', 'paid'])]
        payslip_list = request.env['hr.payslip'].sudo().search(domain)
        data = []
        for payslip in payslip_list:
            worked_days_list = []
            for worked_days in payslip.worked_days_line_ids.filtered(lambda wd: wd.code != 'OUT'):
                worked_days_list.append({
                    'name': worked_days.name,
                    'number_of_hours': worked_days.number_of_hours,
                    'number_of_days': worked_days.number_of_days,
                    'amount': worked_days.amount,
                })
            payslip_lines_list = []
            for line in payslip.line_ids.filtered(lambda l: l.appears_on_payslip):
                payslip_lines_list.append({
                    'name': line.name,
                    'quantity': line.quantity,
                    'total': line.total,
                })
            data.append({
                "payslip_id": payslip.id,
                "employee_id": payslip.employee_id.id,
                "employee_name": payslip.employee_id.name,
                "identification_id": payslip.employee_id.identification_id,
                "children": payslip.employee_id.children,
                "contract_id": payslip.contract_id.id,
                "contract_name": payslip.contract_id.name,
                "contract_type": payslip.employee_id.contract_id.contract_type_id.name,
                "working_schedule": payslip.employee_id.contract_id.hours_per_week,
                "contract_start_date": payslip.employee_id.first_contract_date.isoformat(),
                "date_from": payslip.date_from.isoformat(),
                "date_to": payslip.date_to.isoformat(),
                "computed_on": payslip.compute_date.isoformat(),
                "salary_type": payslip.contract_id.wage_type,
                "basic_salary": payslip.contract_id._get_contract_wage(),
                "worked_days": worked_days_list,
                "payslip_lines": payslip_lines_list,
                "report_pdf_url_en": f"/force_report/pdf/hr_payroll.report_payslip_lang/{payslip.id}",
                "report_html_url_en": f"/force_report/html/hr_payroll.report_payslip_lang/{payslip.id}",
                "report_pdf_url_ar": f"/force_report/pdf/hr_payroll.report_payslip_lang/{payslip.id}/ar",
                "report_html_url_ar": f"/force_report/html/hr_payroll.report_payslip_lang/{payslip.id}/ar",
            })
            # report_payslip_lang
        res = {"result": data}
        return http.Response(json.dumps(res), status=200, mimetype='application/json')

    # Loans
    @validate_token
    @http.route("/api-hr/my-loan", methods=["GET"], type="http", auth="none", csrf=False)
    def api_hr_my_loan(self, **params):
        employee_id = request.context.get("employee_id")
        if not employee_id:
            res = {"result": {"error": "employee_id is missing in context"}}
            return http.Response(json.dumps(res), status=400, mimetype='application/json')
        # employee = request.env['hr.employee'].sudo().browse(employee_id)
        domain = [('employee_id', '=', employee_id)]

        loan_list = request.env['hr.loan'].sudo().search(domain)
        LOAN = request.env['hr.loan'].sudo()
        loan_by_state = [(state, LOAN.concat(*loans)) for state, loans in groupby(loan_list, itemgetter('state'))]
        data = {}
        # def _selection_name(model, field_name, field_value, lang='en_US'):
        #     names = dict(request.env[model].sudo().with_context(lang='ar_001')._fields[field_name]._description_selection(request.env))
        #     return names.get(field_value, field_value)

        # field_description = lambda model, key: request.env['ir.model.fields'].sudo()._get(model, key)['field_description']
        # all_states = ["draft", "confirm", "refuse", "validate1", "validate"]

        # state_info = {
        #     "draft": _("To Submit"),
        #     "waiting_approval_1": _("Submitted"),
        #     "approve": _("Approved"),
        #     "refuse": _("Refused"),
        #     "paid": _("Paid"),
        #     "cancel": _("Cancelled")
        # }

        state_info = self._get_field_selections('hr.loan', 'state')
        for state, loans in loan_by_state:
            # print(f"state: {_selection_name('hr.loan', 'state', state, lang='ar_001')}")
            data[state] = {
                "loan_count": len(loans),
                "description": state_info[state],
                "loans": [{
                    "name": loan.name,
                    "employee_id": {
                        "id": loan.employee_id.id,
                        "name": loan.employee_id.name
                    },
                    "employee_department": {
                        "id": loan.employee_id.department_id.id,
                        "name": loan.employee_id.department_id.display_name
                    },
                    "employee_job": {
                        "id": loan.employee_id.job_id.id,
                        "name": loan.employee_id.job_id.name
                    },
                    "loan_amount": loan.loan_amount,
                    "installment": loan.installment,
                    "payment_date": loan.payment_date.isoformat(),
                    "date": loan.date.isoformat(),
                    "reason": loan.reason,
                    "state": loan.state,
                    "loan_lines": [
                        {
                            'date': line.date.isoformat(),
                            'amount': line.amount,
                            'paid': line.paid,
                        } for line in loan.loan_lines],
                } for loan in loans]
            }
        for state in state_info.keys():
            if state not in data:
                data[state] = {
                    "loan_count": 0,
                    "description": state_info[state],
                    "loans": []
                }
        res = {"result": data}
        return http.Response(json.dumps(res), status=200, mimetype='application/json')

    @validate_token
    @http.route("/api-hr/create-loan", methods=["POST"], type="http", auth="none", csrf=False)
    def api_hr_create_loan(self, **params):
        employee_id = request.context.get("employee_id")
        if not employee_id:
            res = {"result": {"error": "employee_id is missing in context"}}
            return http.Response(json.dumps(res), status=400, mimetype='application/json')
        employee = request.env['hr.employee'].sudo().browse(employee_id)
        # data = request.get_json_data()
        payload = json.loads(request.httprequest.data or '{}')
        try:
            loan = request.env['hr.loan'].sudo().create({
                'employee_id': employee.id,
                'company_id': employee.company_id.id,
                'loan_amount': payload.get('loan_amount'),
                'installment': payload.get('installment'),
                'payment_date': payload.get('payment_date'),
                'reason': payload.get('reason'),
            })
            data = {"msg": "loan created successfully", "loan_id": loan.id}
            res = {"result": data}
            return http.Response(json.dumps(res), status=200, mimetype='application/json')
        except Exception as ex:
            res = {"result": {"error": f"{ex}"}}
            # 406: not acceptable
            return http.Response(json.dumps(res), status=406, mimetype='application/json')

    @validate_token
    @http.route("/api-hr/my-expense", methods=["GET"], type="http", auth="none", csrf=False)
    def api_hr_my_expense(self, **params):
        employee_id = request.context.get("employee_id")
        if not employee_id:
            res = {"result": {"error": "employee_id is missing in context"}}
            return http.Response(json.dumps(res), status=400, mimetype='application/json')
        # employee = request.env['hr.employee'].sudo().browse(employee_id)
        domain = [('employee_id', '=', employee_id)]

        expense_list = request.env['hr.expense'].sudo().search(domain)
        EXPENSE = request.env['hr.expense'].sudo()
        expense_by_state = [(state, EXPENSE.concat(*expenses)) for state, expenses in groupby(expense_list, itemgetter('state'))]
        data = {}

        state_info = self._get_field_selections('hr.expense', 'state')

        for state, expenses in expense_by_state:
            # print(f"state: {_selection_name('hr.loan', 'state', state, lang='ar_001')}")
            data[state] = {
                "expense_count": len(expenses),
                "description": state_info[state],
                "expenses": [{
                    "name": exp.name,
                    "employee_id": {
                        "id": exp.employee_id.id,
                        "name": exp.employee_id.name
                    },
                    "employee_department": {
                        "id": exp.employee_id.department_id.id,
                        "name": exp.employee_id.department_id.display_name
                    },
                    "employee_job": {
                        "id": exp.employee_id.job_id.id,
                        "name": exp.employee_id.job_id.name
                    },
                    "amount": exp.total_amount_currency,
                    # "payment_mode": exp.payment_mode,
                    "date": exp.date.isoformat(),
                    "description": exp.description,
                    "state": exp.state,
                } for exp in expenses]
            }
        for state in state_info.keys():
            if state not in data:
                data[state] = {
                    "expense_count": 0,
                    "description": state_info[state],
                    "expenses": []
                }
        res = {"result": data}
        return http.Response(json.dumps(res), status=200, mimetype='application/json')

    @validate_token
    @http.route("/api-hr/expense-products", methods=["GET"], type="http", auth="none", csrf=False)
    def api_hr_expense_products(self, **params):
        employee_id = request.context.get("employee_id")
        if not employee_id:
            res = {"result": {"error": "employee_id is missing in context"}}
            return http.Response(json.dumps(res), status=400, mimetype='application/json')
        employee = request.env['hr.employee'].sudo().browse(employee_id)
        domain = [('company_id', 'in', [employee.company_id.id, False]), ('can_be_expensed', '=', True)]

        expense_products = request.env['product.product'].sudo().search(domain)

        data = [{
            "id": product.id,
            "name": product.display_name,
        } for product in expense_products]
        res = {"result": data}
        return http.Response(json.dumps(res), status=200, mimetype='application/json')

    @validate_token
    @http.route("/api-hr/create-expense", methods=["POST"], type="http", auth="none", csrf=False)
    def api_hr_create_expense(self, **params):
        employee_id = request.context.get("employee_id")
        if not employee_id:
            res = {"result": {"error": "employee_id is missing in context"}}
            return http.Response(json.dumps(res), status=400, mimetype='application/json')
        employee = request.env['hr.employee'].sudo().browse(employee_id)
        # data = request.get_json_data()
        payload = json.loads(request.httprequest.data or '{}')
        try:
            expense = request.env['hr.expense'].sudo().create({
                'employee_id': employee.id,
                'company_id': employee.company_id.id,
                'currency_id': employee.company_id.currency_id.id,
                'payment_mode': 'own_account',
                'name': payload.get('name'),
                'total_amount_currency': payload.get('amount'),
                'product_id': payload.get('product_id'),
                'date': payload.get('date'),
                'description': payload.get('description'),
                # 'tax_ids': [Command.clear()],
                # 'sample': True,
            })
            data = {"msg": "expense created successfully", "expense_id": expense.id}
            res = {"result": data}
            return http.Response(json.dumps(res), status=200, mimetype='application/json')
        except Exception as ex:
            res = {"result": {"error": f"{ex}"}}
            # 406: not acceptable
            return http.Response(json.dumps(res), status=406, mimetype='application/json')


    # resignation
    @validate_token
    @http.route("/api-hr/my-resignation", methods=["GET"], type="http", auth="none", csrf=False)
    def api_hr_my_resignation(self, **params):
        employee_id = request.context.get("employee_id")
        if not employee_id:
            res = {"result": {"error": "employee_id is missing in context"}}
            return http.Response(json.dumps(res), status=400, mimetype='application/json')
        # employee = request.env['hr.employee'].sudo().browse(employee_id)
        domain = [('employee_id', '=', employee_id), ('resignation_type', '=', 'resignation')]

        resignation_list = request.env['flex.approval.resignation'].sudo().search(domain)
        RESIGNATION = request.env['flex.approval.resignation'].sudo()
        resignation_by_state = [(state, RESIGNATION.concat(*resignations)) for state, resignations in groupby(resignation_list, itemgetter('state'))]
        data = {}
        state_info = self._get_field_selections('flex.approval.resignation', 'state')
        for state, resignations in resignation_by_state:
            # print(f"state: {_selection_name('hr.resignation', 'state', state, lang='ar_001')}")
            data[state] = {
                "resignation_count": len(resignations),
                "description": state_info[state],
                "resignations": [{
                    "name": resignation.name,
                    "employee_id": {
                        "id": resignation.employee_id.id,
                        "name": resignation.employee_id.name
                    },
                    "employee_department": {
                        "id": resignation.employee_id.department_id.id,
                        "name": resignation.employee_id.department_id.display_name
                    },
                    "employee_job": {
                        "id": resignation.employee_id.job_id.id,
                        "name": resignation.employee_id.job_id.name
                    },
                    "resignation_date": resignation.resignation_date and resignation.resignation_date.isoformat(),
                    "resignation_type": resignation.resignation_type,
                    "types_of_end_services": resignation.types_of_end_services,
                    "leave_date": resignation.leave_date and resignation.leave_date.isoformat(),
                    "notice_period": resignation.notice_period,
                    "note": html2plaintext(resignation.note),
                    "approval_request_id": bool(resignation.approval_request_id) and {
                        "id": resignation.approval_request_id.id,
                        "name": resignation.approval_request_id.name,
                        # "state": resignation.approval_request_id.name,
                        "state": self._get_field_selections('approval.request', 'request_status')[resignation.approval_request_id.request_status],
                        "date_confirmed": resignation.approval_request_id.date_confirmed and resignation.approval_request_id.date_confirmed.isoformat(),
                        "reason": html2plaintext(resignation.approval_request_id.reason)
                    },
                    "state": resignation.state,
                } for resignation in resignations]
            }
        for state in state_info.keys():
            if state not in data:
                data[state] = {
                    "resignation_count": 0,
                    "description": state_info[state],
                    "resignations": []
                }
        res = {"result": data}
        return http.Response(json.dumps(res), status=200, mimetype='application/json')

    @validate_token
    @http.route("/api-hr/create-resignation", methods=["POST"], type="http", auth="none", csrf=False)
    def api_hr_create_resignation(self, **params):
        employee_id = request.context.get("employee_id")
        if not employee_id:
            res = {"result": {"error": "employee_id is missing in context"}}
            return http.Response(json.dumps(res), status=400, mimetype='application/json')
        employee = request.env['hr.employee'].sudo().browse(employee_id)
        # data = request.get_json_data()
        payload = json.loads(request.httprequest.data or '{}')
        try:
            resignation = request.env['flex.approval.resignation'].sudo().create({
                'employee_id': employee.id,
                'company_id': employee.company_id.id,
                "resignation_type": 'resignation',
                "types_of_end_services": 'employees_resignation',
                "leave_date": payload.get('leave_date'),
                "notice_period": payload.get('notice_period'),
                "note": payload.get('note'),
            })
            base64_str = payload.get('document')
            if base64_str:
                request.env['ir.attachment'].sudo().create({
                    'name': 'Document',
                    'datas': base64_str,
                    'res_model': 'flex.approval.resignation',
                    'res_id': resignation.id,
                    'type': 'binary',
                })
            data = {"msg": "resignation created successfully", "resignation_id": resignation.id}
            res = {"result": data}
            return http.Response(json.dumps(res), status=200, mimetype='application/json')
        except Exception as ex:
            res = {"result": {"error": f"{ex}"}}
            # 406: not acceptable
            return http.Response(json.dumps(res), status=406, mimetype='application/json')


    # renew_iqama
    @validate_token
    @http.route("/api-hr/my-renew_iqama", methods=["GET"], type="http", auth="none", csrf=False)
    def api_hr_my_renew_iqama(self, **params):
        employee_id = request.context.get("employee_id")
        if not employee_id:
            res = {"result": {"error": "employee_id is missing in context"}}
            return http.Response(json.dumps(res), status=400, mimetype='application/json')
        # employee = request.env['hr.employee'].sudo().browse(employee_id)
        domain = [('employee_id', '=', employee_id)]

        renew_iqama_list = request.env['flex.approval.renew_iqama'].sudo().search(domain)
        IQAMA = request.env['flex.approval.renew_iqama'].sudo()
        renew_iqama_by_state = [(state, IQAMA.concat(*renew_iqamas)) for state, renew_iqamas in groupby(renew_iqama_list, itemgetter('state'))]
        data = {}
        state_info = self._get_field_selections('flex.approval.renew_iqama', 'state')
        for state, renew_iqamas in renew_iqama_by_state:
            # print(f"state: {_selection_name('hr.renew_iqama', 'state', state, lang='ar_001')}")
            data[state] = {
                "renew_iqama_count": len(renew_iqamas),
                "description": state_info[state],
                "renew_iqamas": [{
                    "name": renew_iqama.name,
                    "employee_id": {
                        "id": renew_iqama.employee_id.id,
                        "name": renew_iqama.employee_id.name
                    },
                    "employee_department": {
                        "id": renew_iqama.employee_id.department_id.id,
                        "name": renew_iqama.employee_id.department_id.display_name
                    },
                    "employee_job": {
                        "id": renew_iqama.employee_id.job_id.id,
                        "name": renew_iqama.employee_id.job_id.name
                    },
                    "current_iqama_id": renew_iqama.current_iqama_id,
                    "end_of_iqama": renew_iqama.end_of_iqama and renew_iqama.end_of_iqama.isoformat(),
                    "new_iqama_id": renew_iqama.new_iqama_id,
                    "renewal_date": renew_iqama.renewal_date and renew_iqama.renewal_date.isoformat(),
                    "note": html2plaintext(renew_iqama.note),
                    "state": renew_iqama.state,
                } for renew_iqama in renew_iqamas]
            }
        for state in state_info.keys():
            if state not in data:
                data[state] = {
                    "renew_iqama_count": 0,
                    "description": state_info[state],
                    "renew_iqamas": []
                }
        res = {"result": data}
        return http.Response(json.dumps(res), status=200, mimetype='application/json')

    @validate_token
    @http.route("/api-hr/create-renew_iqama", methods=["POST"], type="http", auth="none", csrf=False)
    def api_hr_create_renew_iqama(self, **params):
        employee_id = request.context.get("employee_id")
        if not employee_id:
            res = {"result": {"error": "employee_id is missing in context"}}
            return http.Response(json.dumps(res), status=400, mimetype='application/json')
        employee = request.env['hr.employee'].sudo().browse(employee_id)
        # data = request.get_json_data()
        payload = json.loads(request.httprequest.data or '{}')
        try:
            renew_iqama = request.env['flex.approval.renew_iqama'].sudo().create({
                'employee_id': employee.id,
                'company_id': employee.company_id.id,
                "new_iqama_id": payload.get('new_iqama_id'),
                "renewal_date": payload.get('renewal_date'),
                "note": payload.get('note'),
            })
            base64_str = payload.get('document')
            if base64_str:
                request.env['ir.attachment'].sudo().create({
                    'name': 'Document',
                    'datas': base64_str,
                    'res_model': 'flex.approval.renew_iqama',
                    'res_id': renew_iqama.id,
                    'type': 'binary',
                })
            data = {"msg": "renew_iqama created successfully", "renew_iqama_id": renew_iqama.id}
            res = {"result": data}
            return http.Response(json.dumps(res), status=200, mimetype='application/json')
        except Exception as ex:
            res = {"result": {"error": f"{ex}"}}
            # 406: not acceptable
            return http.Response(json.dumps(res), status=406, mimetype='application/json')

    # business_trip
    @validate_token
    @http.route("/api-hr/my-business_trip", methods=["GET"], type="http", auth="none", csrf=False)
    def api_hr_my_business_trip(self, **params):
        employee_id = request.context.get("employee_id")
        if not employee_id:
            res = {"result": {"error": "employee_id is missing in context"}}
            return http.Response(json.dumps(res), status=400, mimetype='application/json')
        # employee = request.env['hr.employee'].sudo().browse(employee_id)
        domain = [('employee_id', '=', employee_id)]

        business_trip_list = request.env['flex.approval.business_trip'].sudo().search(domain)
        IQAMA = request.env['flex.approval.business_trip'].sudo()
        business_trip_by_state = [(state, IQAMA.concat(*business_trips)) for state, business_trips in groupby(business_trip_list, itemgetter('state'))]
        data = {}
        state_info = self._get_field_selections('flex.approval.business_trip', 'state')
        for state, business_trips in business_trip_by_state:
            # print(f"state: {_selection_name('hr.business_trip', 'state', state, lang='ar_001')}")
            data[state] = {
                "business_trip_count": len(business_trips),
                "description": state_info[state],
                "business_trips": [{
                    "name": business_trip.name,
                    "employee_id": {
                        "id": business_trip.employee_id.id,
                        "name": business_trip.employee_id.name
                    },
                    "employee_department": {
                        "id": business_trip.employee_id.department_id.id,
                        "name": business_trip.employee_id.department_id.display_name
                    },
                    "employee_job": {
                        "id": business_trip.employee_id.job_id.id,
                        "name": business_trip.employee_id.job_id.name
                    },
                    "trip_type": business_trip.trip_type,
                    "destination": business_trip.destination,
                    "purpose": business_trip.purpose,
                    "start_date": business_trip.start_date and business_trip.start_date.isoformat(),
                    "end_date": business_trip.end_date and business_trip.end_date.isoformat(),
                    "note": html2plaintext(business_trip.note),
                    "state": business_trip.state,
                } for business_trip in business_trips]
            }
        for state in state_info.keys():
            if state not in data:
                data[state] = {
                    "business_trip_count": 0,
                    "description": state_info[state],
                    "business_trips": []
                }
        res = {"result": data}
        return http.Response(json.dumps(res), status=200, mimetype='application/json')

    @validate_token
    @http.route("/api-hr/create-business_trip", methods=["POST"], type="http", auth="none", csrf=False)
    def api_hr_create_business_trip(self, **params):
        employee_id = request.context.get("employee_id")
        if not employee_id:
            res = {"result": {"error": "employee_id is missing in context"}}
            return http.Response(json.dumps(res), status=400, mimetype='application/json')
        employee = request.env['hr.employee'].sudo().browse(employee_id)
        # data = request.get_json_data()
        payload = json.loads(request.httprequest.data or '{}')
        try:
            business_trip = request.env['flex.approval.business_trip'].sudo().create({
                'employee_id': employee.id,
                'company_id': employee.company_id.id,
                "trip_type": payload.get('trip_type'),
                "destination": payload.get('destination'),
                "purpose": payload.get('purpose'),
                "start_date": payload.get('start_date'),
                "end_date": payload.get('end_date'),
                "note": payload.get('note'),
            })
            base64_str = payload.get('document')
            if base64_str:
                request.env['ir.attachment'].sudo().create({
                    'name': 'Document',
                    'datas': base64_str,
                    'res_model': 'flex.approval.business_trip',
                    'res_id': business_trip.id,
                    'type': 'binary',
                })
            data = {"msg": "business_trip created successfully", "business_trip_id": business_trip.id}
            res = {"result": data}
            return http.Response(json.dumps(res), status=200, mimetype='application/json')
        except Exception as ex:
            res = {"result": {"error": f"{ex}"}}
            # 406: not acceptable
            return http.Response(json.dumps(res), status=406, mimetype='application/json')






