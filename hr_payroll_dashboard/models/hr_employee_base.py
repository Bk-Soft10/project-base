# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anfas Faisal K (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from datetime import timedelta
from odoo import models, fields


class HrEmployeeBase(models.AbstractModel):
    _inherit = 'hr.employee.base'

    def _compute_newly_hired(self):
        super()._compute_newly_hired()
        new_hire_field = self._get_new_hire_field()
        new_hire_date = fields.Datetime.now() - timedelta(days=90)
        hire_date = new_hire_date.date() or new_hire_date
        for employee in self:
            emp_hire = employee[new_hire_field]
            if emp_hire and hire_date:
                employee.newly_hired = (employee[new_hire_field] > new_hire_date.date())

