# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    res_partner_use_gmap = fields.Char(string="Google Map API Key1",
                           related="company_id.res_partner_use_gmap", readonly=False, store=True)


class ResCompany(models.Model):
    _inherit = 'res.company'

    res_partner_use_gmap = fields.Char(string="Use Google Map to Fetch Current/Live Address 2")
