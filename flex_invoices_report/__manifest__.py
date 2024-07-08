{
    'name': 'Flex Invoices Reports',
    'version': '17.1.1',
    'summary': 'Generate account move reports based on date range, partner, and invoice type.',
    'description': """
        This module allows users to generate account move reports
        for sale and purchase invoices within a specified date range,
        optionally filtered by partner.
    """,
    'category': 'Accounting',
    'author': 'HACHEMI Mohamed Ramzi || Flex-Ops',
    'website': 'https://www.flex-ops.com',
    'license': 'AGPL-3',
    'depends': ['base', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/account_move_report.xml',
    ],
    'installable': True,
    'auto_install': False,
}
