# -*- coding: utf-8 -*-
{
    'name': 'Flex Detailed Partner Ledger',
    'version': '0.1',
    'summary': 'Detailed Partner Ledger',
    'description': "",
    'category': 'Accounting',
    'author': 'Hossam Zaki, Flex-Ops',
    'website': 'https://www.flex-ops.com',
    'license': 'OPL-1',
    'depends': ['report_xlsx', 'account_reports'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/detailed_partner_ledger.xml',
        'reports/detailed_partner_ledger.xml',
        'reports/reports.xml',
    ],
    'installable': True,
    'auto_install': False,
}
