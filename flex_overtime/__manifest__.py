{
    'name': 'Flex Overtime',
    'version': '1.0',
    'summary': 'Collect Overtime For Employees With Date Period',
    'description': '',
    'category': '',
    'author': 'Sohaib Alamleh||Flex-ops',
    'website': '',
    'license': '',
    'depends': ['web','base','hr', 'hr_attendance', 'hr_contract'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/overtime.xml'
    ],
    'demo': [''],
    'installable': True,
    'auto_install': False,
}