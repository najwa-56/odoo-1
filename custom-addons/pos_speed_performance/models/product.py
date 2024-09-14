# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date


class ProductTemplateSpeed(models.Model):
    _inherit = 'product.template'

    load_pos_default = fields.Boolean('Load POS Default', default=False)
