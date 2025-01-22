{
    'name': 'Flex Delivery Note',
    'version': '0.1',
    'summary': '',
    'description': '',
    'category': '',
    'author': "Hossam Zaki, Flex-Ops",
    'website': "https://flex-ops.com",
    'license': 'OPL-1',
    'depends': ['sale_stock', 'mrp'],
    'data': [
        # security
        'security/groups.xml',
        'security/ir.model.access.csv',
        # views
        'views/delivery_note.xml',
        'views/stock_picking.xml',
        'views/sale_order.xml',
        'views/menus.xml',
        # reports
        'reports/delivery_note.xml',
        # data
        'data/sequence.xml',
    ],
}
