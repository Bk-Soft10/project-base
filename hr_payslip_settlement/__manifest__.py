    #-*- coding:utf-8 -*-
{
    'name': 'Employee Payslip Settlement',
    'summary': 'Customize for  Employee Payslip Settlement',
    'description': "Customize Employee Payslip Settlement",
    'author': "Bksoftware",
    'website': "http://www.bksotware.com",
    'depends': ['base', 'web', 'hr', 'hr_payroll_community'],
    'data': [
        'security/hr_payslip_settlement_security.xml',
        'security/ir.model.access.csv',
        'data/structure_rule_data.xml',
        'views/hr_payslip_settlement_views.xml',
        'views/hr_settlement_type_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
