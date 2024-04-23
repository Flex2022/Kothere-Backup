# -*- coding: utf-8 -*-
{
    'name': "Flex HR Expense",
    'summary': "Manage employee expenses efficiently with Flex HR Expense.",
    'description': """
        Flex HR Expense is a comprehensive solution for managing employee expenses within Odoo.
        This module enhances the functionality of Odoo's HR Expense module, providing additional
        features and customization options tailored to meet your organization's needs.
    """,
    'version': "17.1.1",
    'author': "HACHEMI MOHAMED RAMZI - Flex-Ops",
    'website': "https://flex-ops.com",
    'category': 'Human Resources',
    'license': 'OPL-1',
    'depends': ['base', 'hr_expense'],
    'data': [
        'views/hr_expense.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
