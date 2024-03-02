# -*- coding: utf-8 -*-
{
    'name': "Enforce Inventory Dates",
    'description': """
    - Enforce inventory date in stock transfers
    - Enforce inventory date in inventory adjustment
    """,
    'summary': "",
    'version': "16.0.1",
    'author': "Hossam Zaki - Flex-Ops",
    'website': "https://flex-ops.com",
    'category': '',
    'license': 'OPL-1',
    'price': 100,
    'currency': "EUR",
    'depends': ['base',
                'stock',
                'stock_account',
                ],
    'data': [
        # security
        'security/groups.xml',
        # views
        'views/stock_quant.xml',
        'views/stock_picking.xml',
    ],
    'installable': True,
    'application': False,
}
