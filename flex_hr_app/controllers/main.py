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
            return http.Response(json.dumps(res), status=401, mimetype='application/json')
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
            return http.Response(json.dumps(res), status=401, mimetype='application/json')
        employee = request.env['hr.employee'].sudo().search([('api_username', '=', username)], limit=1)
        if not employee:
            res = {"result": {"error": f"incorrect username"}}
            return http.Response(json.dumps(res), status=401, mimetype='application/json')
        if employee.api_password != password:
            res = {"result": {"error": f"incorrect password"}}
            return http.Response(json.dumps(res), status=401, mimetype='application/json')
        valid_token = request.env['hr.token'].sudo().get_valid_token(employee_id=employee.id, device_token=device_token, create=True)
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
                "image_url": f"/web/image/hr.employee.public/{employee.id}/image_1920",
                # =================================
                "identification_id": employee.identification_id,
                "children": employee.children,
                "contract_id": employee.contract_id.id,
                "contract_name": employee.contract_id.name,
                "contract_type": employee.contract_id.contract_type_id.name,
                "working_schedule": employee.contract_id.hours_per_week,
                "contract_start_date": employee.first_contract_date and employee.first_contract_date.isoformat(),
                "salary_type": employee.contract_id.wage_type,
                "basic_salary": employee.contract_id._get_contract_wage(),
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
                "basic_salary": employee.contract_id._get_contract_wage(),
                # =================================
                "image_url": f"/web/image/hr.employee.public/{employee.id}/image_1920",
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

    # , website=True
    @http.route([
        '/force_report/<converter>/<reportname>.pdf',
        '/force_report/<converter>/<reportname>/<docids>.pdf',
        '/force_report/<converter>/<reportname>/<docids>/<lang>.pdf',
    ], type='http', auth='none')
    def report_routes(self, reportname, docids=None, converter=None, lang=None, **data):
        report = request.env['ir.actions.report'].sudo()
        context = dict(request.env.context)

        if lang == 'ar':
            context.update({'lang': 'ar_001'})
        if docids:
            docids = [int(i) for i in docids.split(',') if i.isdigit()]
        if data.get('options'):
            data.update(json.loads(data.pop('options')))
        if data.get('context'):
            data['context'] = json.loads(data['context'])
            context.update(data['context'])
        if converter == 'html':
            html = report.with_context(context)._render_qweb_html(reportname, docids, data=data)[0]
            return request.make_response(html)
        elif converter == 'pdf':
            pdf = report.with_context(context).sudo()._render_qweb_pdf(reportname, docids, data=data)[0]
            pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
            return request.make_response(pdf, headers=pdfhttpheaders)
        elif converter == 'text':
            text = report.with_context(context)._render_qweb_text(reportname, docids, data=data)[0]
            texthttpheaders = [('Content-Type', 'text/plain'), ('Content-Length', len(text))]
            return request.make_response(text, headers=texthttpheaders)
        else:
            raise werkzeug.exceptions.HTTPException(description='Converter %s not implemented.' % converter)


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






