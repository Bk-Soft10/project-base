import json

from odoo import models

from odoo.addons.base_import import models as model_import

model_import.base_import.MIMETYPE_TO_READER["application/json"] = "json"


class BaseImportJSON(models.TransientModel):
    _inherit = "base_import.import"

    def _read_json(self, record, options):
        items = json.loads(record.file)
        if items:
            headers = items[0].keys()
            yield headers
            for item in items:
                yield [item[header] for header in headers]
