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
from odoo import fields, models


class ProductTemplate(models.Model):
    """Adding the field Arabic name in Products"""
    _inherit = 'product.template'

    product_arabic = fields.Char(string='Arabic name', default="",
                                 help='Here you can set the Arabic name of the'
                                      'Product')
class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    product_arabic = fields.Char(related='product_id.product_tmpl_id.product_arabic', string='Arabic Name', store=True, readonly=True)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_arabic1 = fields.Char(related='product_id.product_tmpl_id.product_arabic', string='Arabic Name', store=True, readonly=True)