{
    'name': 'Flex Maintenance',
    'version': '17.0.1.1',
    'summary': 'Custom Maintenance and repair',
    'description': '',
    'category': '',
    'author': 'Mohamed Mohsen, flex-ops',
    'website': "https://flex-ops.com",
    'license': '',
    'depends': ['base', 'fleet', 'repair', 'maintenance', 'mrp_maintenance', 'purchase'],
    'data': ['views/fleet_vehicle_views.xml',
             'views/maintenance_request_views.xml',
             'views/repair_order_views.xml',
             ],
    'demo': [''],
    'installable': True,
    'auto_install': False,
    'application': True
}