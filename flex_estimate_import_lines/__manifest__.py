{
    'name': 'flex estimate import lines',
    'version': '1.0',
    'summary': 'flex estimate import lines',
    'description': 'flex estimate import lines',
    'category': 'sale',
    'author': 'Abdalrahman Shahrour',
    'website': 'https://flex-ops.com',
    'license': 'AGPL-3',
    'depends': ['bi_job_cost_estimate_customer'],
    'data': ['views/estimate.xml'],
    # 'demo': [''],
    'installable': True,
    'auto_install': False,
    'external_dependencies': {
        'python': ['pandas', 'openpyxl'],
    }
}