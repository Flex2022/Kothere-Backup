# -*- coding: utf-8 -*-
{
    'name': "Flex Stock Reports",
    'version': "17.1.1",
    'summary': "Custom stock reports for Flex-Ops",
    'description': """
        This module provides custom stock reports for Flex-Ops.
    """,
    'category': 'Inventory/Reporting',
    'author': "HACHEMI MOHAMED RAMZI - Flex-Ops",
    'website': "https://flex-ops.com",
    'license': 'OPL-1',
    'depends': ['base', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/stock_slack_report_wizard.xml',
        'reports/purchase_costs_report.xml',
        'views/purchase_views.xml',
        'views/stock.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'images': [
        'static/description/main_screenshot.png',
    ],
    'support': 'support@flex-ops.com',
    'maintainers': [
        'HACHEMI MOHAMED RAMZI <m.hachemi@flex-ops.com>',
    ],
}