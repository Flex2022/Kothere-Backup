{
    'name': 'Flex Repair Customization',
    'version': '17.0.1.1',
    'summary': 'Custom enhancements for the repair management system.',
    'description': """
        This module provides custom functionalities and enhancements 
        to the standard Odoo Repair module, allowing for better 
        management and tracking of repair orders. Features include:
        - Improved UI for repair order views
        - Custom fields and workflows
        - Integration with other modules
    """,
    'category': 'Operations/Repair',
    'author': 'HACHEMI Mohamed Ramzi (Flex-Ops)',
    'website': 'https://flex-ops.com',
    'license': 'OPL-1',
    'depends': ['base', 'repair', 'flex_maintenance','material_purchase_requisitions'],
    'data': [
        'views/repair_order_views.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
