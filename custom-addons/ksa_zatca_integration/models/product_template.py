# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_zatca = fields.Boolean(related="company_id.parent_is_zatca")
    code_type = fields.Char(string="Barcode Code Type",
                            help="it must be in UPC, GTIN, Customs HS Code and multiple other codes")


class ProductProduct(models.Model):
    _inherit = "product.product"

    def get_product_arabic_name(self):
        translations,context = self.get_field_translations('name',['ar_001'])
        for rec in translations:
            if rec.get('lang',False) and rec.get('lang',False) == 'ar_001':
                return rec.get('value','')
        return ''   