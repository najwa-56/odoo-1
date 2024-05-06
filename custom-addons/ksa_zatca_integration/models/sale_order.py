from odoo import api, fields, models, exceptions, _
from decimal import Decimal
import uuid


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        if invoice_vals['partner_id']:
            partner = self.env['res.partner'].sudo().browse(invoice_vals['partner_id'])
            if self.company_id.sudo().zatca_invoice_type == "Standard & Simplified":
                if partner.company_type == 'person':
                    invoice_vals['l10n_sa_invoice_type'] = "Simplified"
                else:
                    invoice_vals['l10n_sa_invoice_type'] = "Standard"
            else:
                invoice_vals['l10n_sa_invoice_type'] = self.company_id.sudo().zatca_invoice_type
        return invoice_vals
