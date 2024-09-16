# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    plu_number = fields.Char(string="PLU Code",inverse='_set_plu_number', size=5 )

    _sql_constraints = [
        ('plu_number_uniq', 'unique(plu_number)', "A PLU Code can only be assigned to one product !"),
    ]

    @api.constrains('plu_number')
    def _constrains_plu_number(self):
        for record in self:
            if record.plu_number:
                if len(record.plu_number) < 4 or not record.plu_number.isdigit():
                    raise ValidationError(_('PLU Number length must be greater than or equal to 4 and must be Integer'))

    def _set_plu_number(self):
        variant_count = len(self.product_variant_ids)
        if variant_count == 1:
            self.product_variant_ids.plu_number = self.plu_number
        elif variant_count == 0:
            self.product_variant_ids.plu_number = self.plu_number
            archived_variants = self.with_context(active_test=False).product_variant_ids
            if len(archived_variants) == 1:
                archived_variants.plu_number = self.plu_number


class ProductProduct(models.Model):
    _inherit = 'product.product'

    plu_number = fields.Char(string="PLU Code",inverse='_set_plu_number',size=5)

    _sql_constraints = [
        ('plu_number_uniq', 'unique(plu_number)', "A PLU Code can only be assigned to one product !"),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        values = super(ProductProduct, self).create(vals_list)
        for vals in vals_list:
            pr_id = self.env['product.template'].search([('id','=',vals.get('product_tmpl_id'))])
            vals['plu_number'] = pr_id.plu_number
        # pos_configs = super().create(vals_list)
        return values

    def _set_plu_number(self):
        template_count = len(self.product_tmpl_id)
        if template_count == 1:
            self.product_tmpl_id.plu_number = self.plu_number

    @api.constrains('plu_number')
    def _constrains_plu_number(self):
        for record in self:
            if record.plu_number:
                if len(record.plu_number) < 4 or not record.plu_number.isdigit():
                    raise ValidationError(_('PLU Number length must be greater than or equal to 4 and must be Integer'))