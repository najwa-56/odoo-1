# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
from markupsafe import Markup
import werkzeug

from odoo import api, fields, Command, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import format_date
from odoo.tools import email_split, float_repr, float_round, is_html_empty


class HrExpense(models.Model):
    _inherit = "hr.expense"

    product_category_id = fields.Many2one(
        comodel_name='product.category',
        string="Product Category",
        related='product_id.categ_id',
        readonly=True,
        store=True
    )
