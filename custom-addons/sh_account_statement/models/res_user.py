# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    sh_company_sign = fields.Text('Signature')