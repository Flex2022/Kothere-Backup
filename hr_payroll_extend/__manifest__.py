# -*- coding: utf-8 -*-
{
    'name': 'HR Payroll Extend',
    'summary': """HR Payroll Customization""",
    'version': '17.0.0.0',
    'author': 'Mahmoud Thaher',
    'website': 'http://www.t2.sa',
    'category': 'Human Resource',
    'depends': ['hr_employee_updation','account','account_check_printing'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/payroll_adjust_request_view.xml',
        #'views/hr_payslip_views.xml',
        'views/hr_variable_increase_views.xml',
        'views/res_config_view.xml',
        'views/hr_department_views.xml',
        'views/account_payent.xml',
        # 'data/data.xml',
        # 'wizard/payroll_comparison.xml',
    ],
    'installable': True,
    'application': False,
}
