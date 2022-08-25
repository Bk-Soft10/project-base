#

{
    "name": "App Employee Self-Service",
    "author": "TBS",
    "version": "1.0",
    "summary": "Use this module to have notification of requirements of "
    "materials and/or external services and keep track of such "
    "requirements.",
    "category": "HR",
    "depends": ['base', 'web', 'hr', 'hr_contract', 'hr_extension', 'analytic', 'hr_expense', 'hr_holidays', 'om_hr_payroll'],
    "license": "LGPL-3",
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        # 'wizard/expanse_wizard.xml',
        'wizard/submit_otp_wizard.xml',
        'data/email_template.xml',
        'data/mail_activity.xml',
        'data/ir_sequence.xml',
        'views/views.xml',
        'views/salary_transfer_views.xml',
        'views/salary_confirmation_views.xml',
        'views/salary_identification_views.xml',
        'views/visa_exit_return_views.xml',
        'views/residency_renewal_views.xml',
        'views/changing_residency_job_views.xml',
        'views/visit_visa_attestation_views.xml',
        'views/benefit_views.xml',
        'views/travel_tickets_views.xml',
        'views/leave_request_views.xml',
        'views/deputation_request_views.xml',
        'views/resignation_request_views.xml',
    ],
    "installable": True,
    "application": True,
}
