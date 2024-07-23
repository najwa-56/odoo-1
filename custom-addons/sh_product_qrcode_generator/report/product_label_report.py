# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from collections import defaultdict

from odoo import _, models
from odoo.exceptions import UserError


def _prepare_data(env, data):
    # change product ids by actual product object to get access to fields in xml template
    # we needed to pass ids because reports only accepts native python types (int, float, strings, ...)
    if data.get('active_model') == 'product.template':
        product_model = env['product.template'].with_context(
            display_default_code=False)
    elif data.get('active_model') == 'product.product':
        product_model = env['product.product'].with_context(
            display_default_code=False)
    else:
        raise UserError(
            _('Product model not defined, Please contact your administrator.'))

    total = 0
    qty_by_product_in = data.get('quantity_by_product')
    # search for products all at once, ordered by name desc since popitem() used in xml to print the labels
    # is LIFO, which results in ordering by product name in the report
    products = product_model.search(
        [('id', 'in', [int(p) for p in qty_by_product_in.keys()])], order='name desc')
    quantity_by_product = defaultdict(list)
    for product in products:
        qty = qty_by_product_in[str(product.id)]
        quantity_by_product[product].append((0, qty))
        total += qty
    if data.get('custom_qr_codes'):
        # we expect custom qr_codes format as: {product: [(qr_code, qty_of_qr_code)]}
        for product, qr_codes_qtys in data.get('custom_qr_codes').items():
            quantity_by_product[product_model.browse(
                int(product))] += (qr_codes_qtys)
            total += sum(qty for _, qty in qr_codes_qtys)

    layout_wizard = env['sh.product.qrcode.generator.label.layout'].browse(
        data.get('layout_wizard'))
    if not layout_wizard:
        return {}

    return {
        'quantity': quantity_by_product,
        'rows': layout_wizard.rows,
        'columns': layout_wizard.columns,
        'page_numbers': (total - 1) // (layout_wizard.rows * layout_wizard.columns) + 1,
        'price_included': data.get('price_included'),
        'extra_html': layout_wizard.extra_html,
    }


class ShReportProductTemplateLabel(models.AbstractModel):
    _name = 'report.sh_product_qrcode_generator.sh_report_product'
    _description = 'Product Label Report'

    def _get_report_values(self, docids, data):
        return _prepare_data(self.env, data)


class ShReportProductTemplateLabelDymo(models.AbstractModel):
    _name = 'report.sh_product_qrcode_generator.sh_report_product_dymo'
    _description = 'Product Label Report'

    def _get_report_values(self, docids, data):
        return _prepare_data(self.env, data)
