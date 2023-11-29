# -*- coding: utf-8 -*-

{
    "name": "Read Only User Access",
    "author": "TBS-IT",
    "version": "1.0",
    "category": "Extra Tools",
    "summary": "Read only user access for particular login user.",
    "description": """ This app provides a functionality to make generic user access read only for a particular login user Set user read only
	restriction on user level. stop user access from the system .user restriction user read only restriction. Restricated user access.
    """,
    "license": "OPL-1",
    "depends": ["base"],
    "data": [
        "data/ir_config_parameter_data.xml",
        "security/user_read_only_group.xml",
        "security/ir.model.access.csv",
        "views/res_user_read_only.xml",
    ],
    "installable": True,
    "auto_install": False,
}
