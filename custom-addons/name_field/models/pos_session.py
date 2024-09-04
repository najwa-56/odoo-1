# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU Odoo Proprietary License
#    v1.0 (OPL-1).
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Odoo Proprietary License v1.0 (OPL-1) for more details.
#
#    You should have received a copy of the GNU Odoo Proprietary License v1.0
#    (OPL-1) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import models


class PosSession(models.Model):
    """Inherited pos session for adding the field product_arabic"""
    _inherit = 'pos.session'

    def _loader_params_product_product(self):
        """Loading the field"""
        result = super()._loader_params_product_product()
        result['search_params']['fields'].append('name_field')
        return result
