# -*- coding: utf-8 -*-
{
    'name': "Flex Sale",
    'description': """
        This module enhances the sales functionality by providing additional features and optimizations for better flexibility and efficiency in managing sales orders.
    """,
    'summary': "Enhance sales processes with additional features and optimizations.",
    'version': "17.1.1",
    'author': "HACHEMI MOHAMED RAMZI - Flex-Ops",
    'website': "https://flex-ops.com",
    'category': 'Sales',
    'license': 'OPL-1',
    'depends': ['base', 'sale'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/sale_order.xml',
        'reports/sale_order_report_templates.xml',
        'wizards/cancel_sale_order_wizard.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
