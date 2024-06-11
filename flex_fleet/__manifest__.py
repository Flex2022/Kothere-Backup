{
    'name': 'Flex Fleet',
    'version': '0.1',
    'summary': 'Fleet Management',
    'description': 'Fleet Management',
    'category': 'Fleet',
    'author': 'Abdalrahman Shahrour',
    'website': 'https://www.flex-ops.com',
    'license': 'AGPL-3',
    'depends': ['base', 'fleet', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/fleet_vehicle.xml',
        'views/stock_picking.xml',
        'wizards/vehicle_report_wizard.xml',

    ],
    'installable': True,
    'auto_install': False,
}
