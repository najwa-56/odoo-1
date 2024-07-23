# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.osv import expression

from io import BytesIO
import base64

try:
    import qrcode
except ImportError:
    qrcode = None


class ShProductTemplate(models.Model):
    _inherit = "product.template"

    sh_qr_code = fields.Char(
        string="QR Code", related='product_variant_ids.sh_qr_code', readonly=False)
    sh_qr_code_img = fields.Binary(
        string="QR Code Image", readonly=False, compute='_compute_sh_qr_code_1')

    def sh_action_open_label_layout_with_qr(self):
        action = self.env['ir.actions.act_window']._for_xml_id(
            'sh_product_qrcode_generator.sh_action_open_label_layout_with_qr')
        action['context'] = {'default_product_tmpl_ids': self.ids}
        return action

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        result = super(ShProductTemplate, self)._name_search(name, domain=domain, operator=operator, limit=limit, order=order)
        if not result:
            if not domain:
                domain = []
            domain = expression.AND([domain, [('sh_qr_code', '=', name)]])
            result = list(self._search(domain, limit=limit, order=order))
        return result

    @api.constrains('sh_qr_code')
    def _validate_qrcode(self):
        for template in self:
            if template.sh_qr_code:
                products = self.env['product.template'].search(
                    [('id', '!=', template.id), ('sh_qr_code', '=', template.sh_qr_code)])
                if products:
                    raise ValidationError("QR code must be unique !")

    def _generate_product_qr_code(self, product, text=None):
        """
            Method of Softhealer Technologies

            This method will generate the QR code for the product.
        """
        if not product:
            return

        if text is None:
            text = self.env['ir.sequence'].next_by_code(
                'seq.sh_product_qrcode_generator')

        if text and qrcode:
            qr_code = qrcode.QRCode(
                version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
            qr_code.add_data(text)
            qr_code.make(fit=True)
            qr_img = qr_code.make_image()
            bytes_io = BytesIO()
            qr_img.save(bytes_io, format="PNG")
            qr_code_image = base64.b64encode(bytes_io.getvalue())

            product.sh_qr_code = text
            product.sh_qr_code_img = qr_code_image

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ShProductTemplate, self).create(vals_list)
        is_create_qr_code = self.env['ir.config_parameter'].sudo().get_param(
            'sh_product_qrcode_generator.is_sh_product_qrcode_generator_when_create')
        if is_create_qr_code:
            for template in res:
                self._generate_product_qr_code(template)

        # Necessary if enter qr code in product template and only 1 variant than should work vice versa
        for vals in vals_list:
            if vals.get("sh_qr_code", False):
                sh_qr_code = vals.get("sh_qr_code")
                if res and res.product_variant_id:
                    res.product_variant_id.sh_qr_code = sh_qr_code
        return res

    @api.depends('sh_qr_code')
    def _compute_sh_qr_code_1(self):
        if self:
            for template in self:
                template.sh_qr_code_img = False
                if template.sh_qr_code:
                    self._generate_product_qr_code(
                        template, text=template.sh_qr_code)
