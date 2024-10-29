{
    'name': 'Flex HR Connector',
    'version': '0.1',
    'summary': 'HR Integration',
    'description': '',
    'category': 'Human Resources',
    'author': "Hossam Zaki, Flex-Ops",
    'website': "https://flex-ops.com",
    'license': 'OPL-1',
    'sequence': 0,
    # 'price': 500.0,
    # 'currency': 'EUR',
    'depends': ['hr',
                'hr_holidays',
                'hr_expense',
                'hr_payroll',
                'nthub_loan_management',
                'flex_kathiri_approvals',
                'hr_attendance',

                ],
    'data': [
        # security
        'security/ir.model.access.csv',
        # views
        'views/hr_token.xml',
        'views/hr_employee.xml',
        'views/hr_notify.xml',
        # reports
        'reports/report.xml',
    ],
    # 'application': True,
    # 'installable': True,
    # 'auto_install': False,
}
