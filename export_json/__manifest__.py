{
    "name": "JSON Export",
    "version": "19.0.1.0.2",
    "category": "Extra Tools",
    "license": "AGPL-3",
    "summary": "Add JSON export to all models similar to XLSX or CSV exports.",
    "author": "Mangono",
    "maintainers": "Mangono",
    "support": "contact@mangono.fr",
    "description": """
JSON Export
===========
see README
""",
    "website": "https://mangono.fr/",
    "depends": ["base", "web"],
    "data": [
        "jsonifier/security/ir.model.access.csv",
    ],
    "demo": [
        "demo/resolver_demo.xml",
        "demo/export_demo.xml",
        "demo/ir.exports.line.csv",
    ],
    "installable": True,
    "images": ["static/description/banner.png"],
}
