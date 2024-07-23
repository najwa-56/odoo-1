# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression


class ShProductProduct(models.Model):
    _inherit = "product.product"

    sh_qr_code = fields.Char(string="QR Code", copy=False)
    sh_qr_code_img = fields.Binary(
        string="QR Code Image", copy=False, compute='_compute_sh_qr_code_2')

    def sh_action_open_label_layout_with_qr(self):
        action = self.env['ir.actions.act_window']._for_xml_id('sh_product_qrcode_generator.sh_action_open_label_layout_with_qr')
        action['context'] = {'default_product_ids': self.ids}
        return action

    @api.constrains('sh_qr_code')
    def _validate_qrcode(self):
        for product in self:
            if product.sh_qr_code:
                products = self.env['product.product'].search(
                    [('id', '!=', product.id), ('sh_qr_code', '=', product.sh_qr_code)])
                if products:
                    raise ValidationError("A QR code must be unique !")

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        result = super(ShProductProduct, self)._name_search(name, domain=domain, operator=operator, limit=limit, order=order)
        if not result:
            if not domain:
                domain = []
            domain = expression.AND([domain, [('sh_qr_code', '=', name)]])
            result = list(self._search(domain, limit=limit, order=order))
        return result

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ShProductProduct, self).create(vals_list)
        is_create_qr_code = self.env['ir.config_parameter'].sudo().get_param(
            'sh_product_qrcode_generator.is_sh_product_qrcode_generator_when_create')
        if is_create_qr_code:
            for product in res:
                self.env["product.template"]._generate_product_qr_code(product)
        return res

    @api.depends('sh_qr_code')
    def _compute_sh_qr_code_2(self):
        if self:
            for product in self:
                product.sh_qr_code_img = False
                if product.sh_qr_code:
                    self.env["product.template"]._generate_product_qr_code(
                        product, text=product.sh_qr_code)
