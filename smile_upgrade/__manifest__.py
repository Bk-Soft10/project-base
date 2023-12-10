{
    "name": "Database Upgrade",
    "version": "1.0",
    "depends": ["web"],
    "author": "Smile",
    "license": "AGPL-3",
    "description": "",
    "summary": "",
    "website": "",
    "category": "Tools",
    "sequence": 20,
    "auto_install": False,
    "installable": True,
    "application": False,
    "assets": {
        "web.assets_backend": [
            "smile_upgrade/static/src/**/*",
        ],
    },
    "images": ["static/description/banner.gif"],
}
