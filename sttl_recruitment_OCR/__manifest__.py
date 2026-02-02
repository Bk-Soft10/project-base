# __manifest__.py
{
    'name': 'OCR Recruitment',
    'version': '19.0.1.0',
    'license': 'LGPL-3',
    'category': 'Tools',
    'author': "Silver Touch Technologies Limited",
    'website': "https://www.silvertouch.com/",
    'summary': 'Extracts the information of candidates from the resumes and creates applications in recruitment.',
    'depends': ['base', 'web', 'sms', 'hr_recruitment', 'base_setup'],
    
    'assets': {
        'web.assets_backend': [
            'sttl_recruitment_OCR/static/src/js/inherited_applicant_tree_view.js',
            'sttl_recruitment_OCR/static/src/xml/inherited_applicant_tree_view.xml',
        ],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/view_upload_documents.xml',
        'views/inherited_recruitent_form_view.xml',
        'views/res_config_view.xml',
        "data/source_data.xml",

    ],
    'external_dependencies': {
        'python': ['pypdf', 'pdf2image', 'pytesseract', 'Pillow', 'python-docx' ],
    },
    'images': ['static/description/banner.png'],

    'installable': True,
    'application': True,
}
