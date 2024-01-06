# -*- coding: utf-8 -*-
{
    'name': 'Flex Sales / Purchase Features',
    'version': '17.0.0.0',
    'description': """""",
    'summary': '',
    'author': "Hossam Zaki, Flex-Ops",
    'website': "https://flex-ops.com",
    'depends': ['base',
                'mail',
                'sale',
                'sale_management',
                # 'sale_crm',
                # 'purchase',
                # 'is_customer_is_vendor',
                # 'account_asset',
                # 'hr',
                # 'ma_protech_mrp'
                ],
    'data': [
        'security/groups.xml',
        # 'data/mail_template.xml',
        # 'views/res_partner.xml',
        'views/sale.xml',
        'views/setting.xml'
        # 'views/purchase.xml',
        # 'data/ir_sequence.xml',
        # 'data/ir_rule.xml',
    ],
    'installable': True,
    'auto_install': False,
}
