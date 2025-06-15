{
    'name': 'Flex Weight PO',
    'version': '1.0',
    'summary': 'Flex Weight Purchase Order',
    'description': 'This module allows you to manage weight-based purchase orders in Odoo. It integrates with the purchase and stock modules to handle products based on their weight.',
    'category': 'Inventory Management',
    'author': 'Sohaib Alamleh||Flex-ops',
    'website': 'https://www.flex-ops.com',
    'license': 'LGPL-3',
    'depends': ['base', 'purchase_stock', 'fleet'],
    'data': ['security/groups.xml',
             'security/ir.model.access.csv',
             'data/ir_sequence_data.xml',
             'views/weight_po.xml',
             'views/purchase.xml'
             ],
    'installable': True,
    'auto_install': False,
}