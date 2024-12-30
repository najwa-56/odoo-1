from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import ValidationError, UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'


    def button_validate(self):
        """
        Override the button_validate method to create a record in the multicompany.transfer.stock model
        """
        res = super(StockPicking, self).button_validate()
        
        for picking in self:
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

                if not destination_location:
                    raise UserError("No destination location found with for Dolfin")

                # Prepare lines for the transfer
                transfer_lines = []
                for move_line in picking.move_line_ids:
                    transfer_lines.append((0, 0, {
                        'ks_product_id': move_line.product_id.id,
                        'ks_qty_transfer': move_line.quantity,
                        'ks_product_uom_type':move_line.product_uom_id.id,
                    }))

                # Create multicompany.transfer.stock record
                transfer_id = self.env['multicompany.transfer.stock'].sudo().create({
                    'ks_transfer_to': destination_company.id,
                    'ks_transfer_to_location': destination_location.id,
                    'ks_transfer_from': picking.company_id.id,
                    'ks_transfer_from_location': picking.location_id.id,
                    'ks_memo_for_transfer': f"Transfer from Picking {picking.name}",
                    'ks_schedule_date': fields.Date.today(),
                    'ks_multicompany_transfer_stock_ids': transfer_lines,
                    'state': 'draft',
                })

                transfer_id.ks_check_availability()
                # transfer_id.ks_confirm_inventory_transfer()

        return res



class StockLocation(models.Model):
    _inherit = 'stock.location'

    is_inter = fields.Boolean('Factory Source Location?')
    is_inter_dolfin = fields.Boolean('Dolfin Location?')
    is_from_inter = fields.Boolean('Factory Dolfin Location?')
    

    transfer_to = fields.Selection([
        ('brek', 'Al Brek'),
        ('abobaker', 'Abo Baker'),
        ('zolfie', 'Al Zolfie'),
    ], string='Transfer To' )
    

    transfer_type = fields.Selection([
        ('raw', 'Raw'),
        ('product', 'Product'),
    ], string='Transfer Type' )
