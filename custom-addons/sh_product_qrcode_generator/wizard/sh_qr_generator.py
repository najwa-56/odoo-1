# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.


from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ShProductQRCodeGeneratorWizard(models.TransientModel):
    _name = 'sh.product.qrcode.generator.wizard'
    _description = 'Product QR Code Generator Wizard'

    product_tmpl_ids = fields.Many2many(
        'product.template', string='Products', copy=False)
    product_var_ids = fields.Many2many(
        'product.product', string='Product Variants', copy=False)
    # Generate Barcode for Existing Product
    is_overwrite_existing = fields.Boolean("Overwrite QR code If Exists")

    @api.model
    def default_get(self, default_fields):
        rec = super(ShProductQRCodeGeneratorWizard,self).default_get(default_fields)

        active_ids = self._context.get('active_ids')
        active_model = self._context.get('active_model')

        if not active_ids:
            raise UserError(_("Programming error: wizard action executed without active_ids in context."))

        if active_model == 'product.template':
            products = self.env['product.template'].browse(active_ids)
            rec.update({'product_tmpl_ids': [(6, 0, products.ids)]})

        elif active_model == 'product.product':
            products = self.env['product.product'].browse(active_ids)
            rec.update({'product_var_ids': [(6, 0, products.ids)]})

        return rec

    def action_generate_qr_code(self):
        if self.user_has_groups('sh_product_qrcode_generator.group_sh_product_qr_code_generator'):

            # Product Template
            if self.product_tmpl_ids:
                for product in self.product_tmpl_ids:
                    if product.sh_qr_code and self.is_overwrite_existing:
                        self.env["product.template"]._generate_product_qr_code(
                            product)

                    elif not product.sh_qr_code:
                        self.env["product.template"]._generate_product_qr_code(
                            product)

            # Product Variant
            elif self.product_var_ids:
                for product in self.product_var_ids:
                    if product.sh_qr_code and self.is_overwrite_existing:
                        self.env["product.template"]._generate_product_qr_code(
                            product)

                    elif not product.sh_qr_code:
                        self.env["product.template"]._generate_product_qr_code(
                            product)

        else:
            raise UserError(
                "You don't have rights to generate product QR Code")
