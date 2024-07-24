from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Inheritmulti_uom(models.Model):

    _inherit = 'product.multi.uom.price'
    barcode = fields.Char('Barcode')
    product_variant_id =fields.Many2one('product.product',related="product_id.product_variant_id",store=True)
    product_variant_count = fields.Integer('Product Variant Count')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    multi_uom_price_barcode = fields.Char(
        string='Barcode',
        compute='_compute_multi_uom_price_barcode',
        store=True
    )

    @api.depends('multi_uom_price_id')
    def _compute_multi_uom_price_barcode(self):
        for record in self:
            if record.multi_uom_price_id:
                # If you want to concatenate all barcodes into one string
                barcodes = record.multi_uom_price_id.mapped('barcode')
                record.multi_uom_price_barcode = ', '.join(filter(None, barcodes))
            else:
                record.multi_uom_price_barcode = ''


    @api.model
    def search_product_by_barcode(self, barcode):
        # Search for the `product.multi.uom.price` record with the given barcode
        uom_price_records = self.env['product.multi.uom.price'].search([('barcode', '=', barcode)])
        if uom_price_records:
            # Return the product.template linked to the found `product.multi.uom.price` records
            return uom_price_records.mapped('product_id.product_tmpl_id')
        return self.env['product.template']


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _search_product_by_barcode(self, barcode):
        # Call the search_product_by_barcode method from the product.template model
        product_template = self.env['product.template'].search_product_by_barcode(barcode)
        if product_template:
            return product_template[0]  # Assuming you only want one result
        return False

    @api.model
    def create_or_update_order_line_from_barcode(self, order_id, barcode, qty=1.0):
        # Find the product template using the barcode
        product_template = self._search_product_by_barcode(barcode)

        if product_template:
            # Check if the product already exists in the order
            existing_line = self.search(
                [('order_id', '=', order_id), ('product_id.product_tmpl_id', '=', product_template.id)])

            if existing_line:
                # Update the existing line
                existing_line.write({'product_uom_qty': existing_line.product_uom_qty + qty})
            else:
                # Create a new order line
                self.create({
                    'order_id': order_id,
                    'product_id': product_template.product_variant_id.id,
                    'product_uom_qty': qty,
                    'price_unit': product_template.product_variant_id.lst_price,
                })
        else:
            raise UserError("Product with barcode {} not found.".format(barcode))