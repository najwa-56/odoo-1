# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class ResCompany(models.Model):
    _inherit = 'res.company'

    multi_barcode_for_product = fields.Boolean(string="Multi Barcode For Product")

