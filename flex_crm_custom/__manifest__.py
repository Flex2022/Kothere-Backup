# -*- coding: utf-8 -*-
{
    'name': "Flex CRM",
    'description': """
        Enhance your CRM capabilities with this module, providing additional features and optimizations for more effective customer relationship management.
    """,
    'summary': "Optimize and extend CRM functionality for improved customer relationship management.",
    'version': "17.1.1",
    'author': "HACHEMI MOHAMED RAMZI - Flex-Ops",
    'website': "https://flex-ops.com",
    'category': 'Customer Relationship Management',
    'license': 'OPL-1',
    'depends': ['base', 'sale', 'crm', 'sale_crm','account','analytic'],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_lead.xml',
        'views/settings.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
