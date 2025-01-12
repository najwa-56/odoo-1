from odoo import api, fields, models, exceptions


class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    payment_journal_id = fields.Many2one('account.journal', string='Payment Journal')

    def action_print_standard_invoice(self):
        if self.invoice_ids:
            return self.env.ref('ksa_zatca_integration.action_report_standard_low_margin_tax_invoice').report_action(self.invoice_ids.ids)

    # @api.onchange('partner_id', 'sale_order_template_id')
    # def onchange_partner_id_dolfin(self):
    #     for order in self:
    #         if order.partner_id and order.partner_id.is_dolfin:
    #             for line in order.order_line:
    #                 # Remove taxes
    #                 line.tax_id = False
    #                 # Adjust price_unit by subtracting 15%
    #                 if line.price_unit:
    #                     line.price_unit = line.price_unit / 1.15



   
  

  

    def action_confirm(self):
        res = super(SaleOrder, self.with_context(default_immediate_transfer=True)).action_confirm()
        for order in self:
            warehouse = order.warehouse_id
            if warehouse.is_delivery_set_to_done and order.picking_ids: 
                for picking in self.picking_ids:
                    if picking.state == 'cancel':
                        continue
                    for move in picking.move_ids:
                        move.quantity = move.product_qty
                    picking._autoconfirm_picking()
                    picking.button_validate()
                    for move_line in picking.move_ids_without_package:
                        move_line.quantity = move_line.product_uom_qty
                    
                    for mv_line in picking.move_ids.mapped('move_line_ids'):
                        # if not mv_line.button_validate and mv_line.reserved_qty or mv_line.reserved_uom_qty:
                        mv_line.quantity = mv_line.quantity_product_uom#.reserved_qty or mv_line.reserved_uom_qty

                    picking._action_done()


                    if picking.partner_id and picking.partner_id.is_dolfin:
                        destination_company = self.env['res.company'].sudo().search([
                            ('company_registry', '=', '1131156025')
                        ], limit=1)

                        if not destination_company:
                            raise UserError("No company found with the registry 1131156025")


                        destination_location = self.env['stock.location'].sudo().search([
                            ('is_inter_dolfin', '=', True),
                            ('company_id', '=', destination_company.id)
                        ], limit=1)

                        source_location = self.env['stock.location'].sudo().search([
                            ('is_from_inter', '=', True),
                            ('company_id', '=', picking.company_id.id)
                        ], limit=1)

                        if not destination_location:
                            raise UserError("No destination location found with for Dolfin")

                        
                        if not source_location:
                            raise UserError("No Source location found with for Dolfin")


                        transfer_id = self.env['multicompany.transfer.stock'].sudo().create({
                            'ks_transfer_to': destination_company.id,
                            'ks_transfer_to_location': destination_location.id,
                            'ks_transfer_from': picking.company_id.id,
                            'ks_transfer_from_location': source_location.id,
                            'ks_memo_for_transfer': f"Transfer from Picking {picking.name}",
                            'ks_schedule_date': fields.Date.today(),
                            'state': 'draft',
                            'ks_multicompany_transfer_stock_ids': [
                                (0, 0, {
                                    'ks_product_id': move_line.product_id.id,
                                    'ks_qty_transfer': move_line.product_qty,
                                    'ks_product_uom_type': move_line.product_uom.id,
                                }) for move_line in picking.move_ids
                            ]
                        })
                        transfer_id.ks_check_availability()
                        transfer_id.ks_confirm_inventory_transfer()




            if warehouse.create_invoice and not order.invoice_ids:
                order._create_invoices()
            if warehouse.validate_invoice and order.invoice_ids:
                for invoice in order.invoice_ids:
                    if invoice.partner_id.is_dolfin:
                        journal_id = self.env['account.journal'].search([('is_dolfin','=',True)])
                        if not journal_id:
                            raise UserError("No Jouranl with is_dolfin is set")
                        if journal_id:
                            invoice.write({
                                'journal_id':journal_id.id
                            })
                    invoice.action_post()

                    payment_register = self.env['account.payment.register'].with_context(active_model='account.move',active_ids=invoice.ids).create(
                        {
                        'payment_date': invoice.date,
                        'journal_id':order.payment_journal_id.id
                    })
                    payment_register.action_create_payments()

        return res  



class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    
   
    @api.onchange('product_uom_qty')
    def onchange_partner_id_dolfin(self):
        sale_zero_taxes = self.env['account.tax'].search([
                    ('type_tax_use', '=', 'sale'),
                    ('amount', '=', 0)])

        

        for line in self:
            if line.order_id.partner_id and line.order_id.partner_id.is_dolfin:
                # Remove taxes
                line.tax_id = [(5, 0, 0)]
                line.tax_id = [(4, tax.id, 0) for tax in sale_zero_taxes]
                # Adjust price_unit by subtracting 15%
                if line.price_unit:
                    line.price_unit = line.price_unit / 1.15
                