# -*- coding: utf-8 -*-
#################################################################################
#################################################################################
{
  "name":  "Print Odoo Reports via Zebra Printer",
  "summary":  """This module allows the user to directly print the reports via zebra printer instead of downloading as PDF.""",
  "category":  "Extra Tools",
  "version":  "0.4",
  "author":  "Webkul Software Pvt. Ltd.",
  "license":  "Other proprietary",
  "website":  "https://store.webkul.com/",
  "description":  """This module allows the user to directly print the reports via zebra printer instead of downloading as PDF.""",
  "depends":  ['base'],
  "live_test_url":  "http://odoodemo.webkul.com/demo_feedback?module=wk_odoo_directly_print_reports",
  "data":  [
      'security/ir.model.access.csv',
      'views/ir_actions_report_xml_view.xml',
      'views/report_template_view.xml',
      'views/printers_view.xml',
      'views/templates.xml',
  ],
  "images":  ['static/description/Banner.png'],
  "application":  True,
  "installable":  True,
  # "pre_init_hook":  "pre_init_check",
  #  "external_dependencies":  {'python': ['zplgrf']},
}