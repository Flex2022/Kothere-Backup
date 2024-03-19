{
    'name': 'Flex Employee Sales',
    'version': '1.0',
    'summary': 'Flex Employee Sales',
    'description': 'Flex Employee Sales',
    'category': 'Sales',
    'author': 'Abdalrahman Shahrour',
    'website': 'https://www.flex-ops.com',
    'license': 'AGPL-3',
    'depends': ['base', 'sale', 'account', 'hr', 'hr_payroll', 'l10n_sa_hr_payroll'],
    'data': [
        'views/sale_order.xml',
        'views/invoice.xml',
        'views/hr_payslip.xml',
        'views/contract.xml',
        'data/cron_job.xml',
    ],

    'installable': True,
    'auto_install': False,
}