# -*- coding: utf-8 -*-
{
    'name': 'Flex Purchase Types',
    'version': '17.0.0.1',
    'description': "",
    'author': "Hossam Zaki, Flex-Ops",
    'website': "https://flex-ops.com",
    'depends': ['purchase',
                ],
    'data': [
        # security
        'security/ir.model.access.csv',
        # views
        'views/purchase_order.xml',
        'views/purchase_type.xml',
        'views/res_users.xml',
    ],
}
