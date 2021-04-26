{
    "name": "Slnee LDAPS authentication",
    "version": "13.0.1.0.1",
    "category": "Tools",
    "website": "https://github.com/OCA/server-auth",
    "author": "slnee",
    "license": "AGPL-3",
    "installable": True,
    "application": False,
    "summary": "Allows to use LDAP over SSL authentication",
    "depends": ["auth_ldap"],
    "data": [
        "views/res_company_ldap_views.xml"
    ],
    "external_dependencies": {"python": ["python-ldap"]},
}
