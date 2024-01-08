# -*- coding: utf-8 -*-
{
    'name': "Sale Category Domain",
    'description': """
    - Restricted Access For Product Category For Specific Company
    """,
    'summary': "",
    'version': "16.0.1",
    'author': "Sohaib Alamleh - Flex-Ops",
    'website': "https://flex-ops.com",
    'category': '',
    'license': 'OPL-1',
    'depends': ['base',
                'contacts',
                'product',
                'account',
                'account_accountant',
                'stock',
                ],
    'data': [
        # security
        'views/company.xml',
        # 'data/company.xml',
    ],
    'installable': True,
    'application': False,
}
