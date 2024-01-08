# -*- coding: utf-8 -*-
{
    'name': "Flex SALES DAY BOOK REPORT",
    'description': """
        This module adds a wizard for generating Sales Book Day Report.
    """,
    'summary': "Generate Sales Day Book Report",
    'version': "17.1.1",
    'author': "HACHEMI MOHAMED RAMZI - Flex-Ops",
    'website': "https://flex-ops.com",
    'category': 'Sales',
    'license': 'OPL-1',
    'depends': ['base', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/sale_day_book_wizard.xml',
        'reports/sale_day_book_report.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
