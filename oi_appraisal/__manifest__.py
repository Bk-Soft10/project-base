{
    "name": "Employee Appraisals",
    "summary": "Evaluations, Periodical Evaluations, Appraisals, Surveys for Employee, Employee Rating, 360 Appraisal, 360 Feedback, 360 Evaluation, Employee Statistics, 365 Appraisal, 365 Feedback, 365 Evaluation",    
    'category': 'Human Resources',
    "description": """
        Employee Appraisals.
         
    """,
    
    "author": "Openinside",
    "license": "OPL-1",
    'website': "https://www.open-inside.com",
    "version": "13.0.1.3.3",
    "price" : 99.99,
    "currency": 'EUR',
    "installable": True,
    'application': True,
    "depends": [
        'hr', 'oi_workflow'
    ],
    "data": [
        'security/res_groups.xml',
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        'data/appraisal_rate.xml',
        'data/approval_config.xml',
        'data/ir_sequence.xml',
        'view/action.xml',
        'view/appraisal_batch.xml',
        'view/appraisal_question.xml',
        'view/appraisal_rate.xml',
        'view/appraisal_section.xml',
        'view/appraisal_template.xml',        
        'view/appraisal.xml',
        'view/appraisal_generate.xml',
        'view/hr_job.xml',
        'view/appraisal_batch_type.xml',        
        'view/menu.xml'
    ],
    'images': [
        'static/description/cover.png'
    ],
    'odoo-apps' : True      
}

