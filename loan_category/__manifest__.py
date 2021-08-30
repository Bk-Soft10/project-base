
{
    "name": "loan category",
    "author": "Bk Software",
    "version": "1.0",
    "summary": "Use this module to have notification of requirements of "
    "materials and/or external services and keep track of such "
    "requirements.",
    "category": "Custom Management",
    "depends": ["base", "web", "ohrms_loan_accounting", "ohrms_loan"],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_loan_category.xml',
    ],
    "license": "LGPL-3",
    "installable": True,
    "application": True,
}
