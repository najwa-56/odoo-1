# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models


class ProductTemplate(models.Model):
    _name = "product.template"
    _inherit = ["barcodes.barcode_events_mixin", "product.template"]

    def on_barcode_scanned(self, barcode):
        self.barcode = barcode


class ProductProduct(models.Model):
    _name = "product.product"
    _inherit = ["barcodes.barcode_events_mixin", "product.product"]

    def on_barcode_scanned(self, barcode):
        self.barcode = barcode
