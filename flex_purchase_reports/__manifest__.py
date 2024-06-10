# -*- coding: utf-8 -*-
{
    'name': "Flex Purchase Reports",
    'description': """
        This module add the Purchase Reports functionality in Odoo, providing additional features and improvements.
    """,
    'summary': "Purchase Reports",
    'version': "17.1.1",
    'author': "HACHEMI MOHAMED RAMZI - Flex-Ops",
    'website': "https://flex-ops.com",
    'category': 'Inventory/Purchase',
    'license': 'OPL-1',
    'depends': ['base', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/purchase_cost_report_wizard.xml',
        'reports/purchase_costs_report.xml',
        'reports/purchase_agreement_report.xml',
        'views/purchase_views.xml',

    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
