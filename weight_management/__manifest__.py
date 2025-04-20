# -*- coding: utf-8 -*-
{
    'name': "Weigh Bridge Calculations",
    'category': 'Warehouse',
    'author': "AppsComp Widgets Pvt Ltd",
    "live_test_url": "https://www.youtube.com/watch?v=zsSYziCKwhg",
    'website': "http://www.appscomp.com",
    'images': ['static/description/banner.png'],
    #'images': ['static/description/banner.gif'],
    'version': '17.0',
    'license': 'LGPL-3',
    'description': 'The Weigh Bridge Calculations Management manages the Single Product or goods '
                   'that are being delivered can pass through weigh bridge calculations,'
                   'along with <q>an Approval</q> process as been executed.',
    'sequence': 10,
    'price': '25',
    #'price': '20.76',
    'currency': 'EUR',
    'summary': """
        It is used to measure single products or goods that include an approval process.
        """,
    # any module necessary for this one to work correctly
    'depends': ['base', 'sale_management', 'account', 'stock', 'product'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        # 'report/weightreport.xml',
        'wizard/weight_management_wizard_view.xml',
        'views/config.xml',
        'views/report/weigh_bridge_report .xml',
        'views/stock_picking.xml',
        'views/weight_management.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
