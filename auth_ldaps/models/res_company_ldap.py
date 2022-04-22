# Copyright (C) Creu Blanca
# Copyright (C) 2018 Brainbean Apps
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


import logging

import ldap

from odoo import fields, models

_logger = logging.getLogger(__name__)


class CompanyLDAP(models.Model):
    _inherit = "res.company.ldap"
    _description = "Company LDAP configuration"

    api_student_user = fields.Many2one('res.users', string='Template Api-Student User', help="User to copy when creating new users")
    api_employee_user = fields.Many2one('res.users', string='Template Api-Employoee User',
                                   help="User to copy when creating new users")
    # is_ssl = fields.Boolean(string="Use LDAPS", default=False)
    # skip_cert_validation = fields.Boolean(
    #     string="Skip certificate validation", default=False
    # )

    def _get_ldap_dicts(self):
        res = super()._get_ldap_dicts()
        for rec in res:
            ldap = self.sudo().browse(rec["id"])
            rec["api_student_user"] = ldap.api_student_user or False
            rec["api_employee_user"] = ldap.api_employee_user or False
        return res



    def _connect(self, conf):
        """
        Connect to an LDAP server specified by an ldap
        configuration dictionary.

        :param dict conf: LDAP configuration
        :return: an LDAP object
        """

        uri = 'ldap://%s:%d' % (conf['ldap_server'], conf['ldap_server_port'])

        connection = ldap.initialize(uri)
        connection.protocol_version = ldap.VERSION3
        connection.set_option(ldap.OPT_REFERRALS, 0)
        if conf['ldap_tls']:
            connection.start_tls_s()
        _logger.info("oooooooooooooooooooooooooooooooooooooooooooo ", connection)
        return connection

    # def _get_or_create_user(self, conf, login, ldap_entry):
    #     _logger.info("ldab_eeeeeeeeeeeeeeeeeee ", ldap_entry)
    #     return super(CompanyLDAP, self)._get_or_create_user(conf, login, ldap_entry)
    #
    # def _query(self, conf, filter, retrieve_attributes=None):
    #     res = super(CompanyLDAP, self)._query(conf, filter, retrieve_attributes=None)
    #     _logger.info("_queryyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy ", res)
    #     return res
    #
    # def _map_ldap_attributes(self, conf, login, ldap_entry):
    #     _logger.info("_map_ldap_attributes ldab_eeeeeeeeeeeeeeeeeee ", ldap_entry)
    #     res = super(CompanyLDAP, self)._map_ldap_attributes(conf, login, ldap_entry)
    #     _logger.info("_queryyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy ", res)
    #     return res
    #
    # def _get_or_create_user(self, conf, login, ldap_entry):
    #     _logger.info("_get_or_create_user ldab_eeeeeeeeeeeeeeeeeee ", ldap_entry)
    #     return super(CompanyLDAP, self)._get_or_create_user(conf, login, ldap_entry)