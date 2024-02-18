# -*- coding: utf-8 -*-
###################################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Jesni Banu (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
{
    'name': 'Open HRMS Employee Info',
    'version': '17.0.0.0',
    'summary': """Adding Advanced Fields In Employee Master""",
    'description': 'This module helps you to add more information in employee records.',
    'category': 'Generic Modules/Human Resources',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': "https://www.openhrms.com",
    'depends': ['base','contacts', 'hr', 'mail', 'hr_contract', 'hr_expense','hr_payroll','account','analytic','hr_appraisal'],
    'data': [
        'security/hr_security.xml',
        'security/ir.model.access.csv',
        # 'security/ir_rule.xml',
        'data/data.xml',
        # 'views/director_staff_view.xml',
        'views/contract_days_view.xml',
        # 'views/updation_config.xml',
        'views/hr_employee_view.xml',
        # 'views/hr_notification.xml',
        # 'views/hr_employee_profile_view.xml',
        'views/hr_office_location_view.xml',
        # 'views/request_status_view.xml',
        # 'views/assets.xml',
        'views/salary_increase_view.xml',
        'views/appresal.xml',
        # 'views/hr_employee_provision_view.xml',
        # 'report/report_saudicontract.xml',
        # 'report/experience_certificate.xml',
        # 'report/disclaimer.xml',
        # 'report/salary_definition.xml',
        # 'report/end_service_liquidation_form.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hr_employee_updation/static/src/css/main.css',
        ],
    },
    'demo': [],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
