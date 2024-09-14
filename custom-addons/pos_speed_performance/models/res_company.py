# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    x_allow_online_search = fields.Boolean('Allow Online Search', default=False)
    x_limit_partner = fields.Integer('Number of Customer Loading', default=50, required=True)
    x_limit_product = fields.Integer('Number of Product Loading', default=50, required=True)