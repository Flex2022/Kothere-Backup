# -*- coding: utf-8 -*-
{
    'name': 'Firebase Messaging Integration',
    'description': """""",
    'version': '17.0.0.1',
    'author': "Hossam Zaki - Flex-Ops",
    'website': "https://flex-ops.com",
    'category': '',
    'license': 'OPL-1',
    'depends': ['hr'],
    'data': [
        # views
        'views/res_config_settings.xml',
    ],
    'installable': True,
    'auto_install': False,
    'external_dependencies': {
        'python': ['google-api-python-client']
    },
}
