# -*- coding: utf-8 -*-
from odoo import fields, models, api, exceptions
import logging
_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    zatca_compliance_invoices_api = fields.Html(readonly=1, related='account_move.zatca_compliance_invoices_api')
    l10n_sa_zatca_status = fields.Char(related='account_move.l10n_sa_zatca_status')
    zatca_status_code = fields.Char(related='account_move.zatca_status_code')
    zatca_invoice_name = fields.Char(copy=False, related='account_move.zatca_invoice_name')
    account_move_state = fields.Selection(string='Status ', related='account_move.state')
    l10n_sa_invoice_type = fields.Selection(string="Invoice Type", related='account_move.l10n_sa_invoice_type')

    def send_for_reporting(self):
        self.account_move.send_for_reporting(no_xml_generate=1)

    def get_simplified_zatca_report(self, pos_reference):
        self = self.sudo().search([('pos_reference', '=', pos_reference)])
        if not self.company_id.zatca_send_from_pos:
            if len(self.refunded_order_ids.account_move.ids) > 1:
                raise exceptions.ValidationError("only 1 invoice can be returned at a time.")
                
        report_action = self.env.ref('ksa_zatca_integration.action_report_simplified_tax_invoice').sudo()
        return self.env['ir.actions.report']._render_qweb_html(report_action, self.account_move.ids)[0].decode('utf-8')

    def _prepare_invoice_vals(self):
        invoice_vals = super(PosOrder, self)._prepare_invoice_vals()
        invoice_vals['l10n_sa_invoice_type'] = 'Simplified'
        return invoice_vals

    @api.model
    def create_from_ui(self, orders, draft=False):
        order_ids = super(PosOrder, self).create_from_ui(orders, draft=draft)
        for order_id in order_ids:
            self_id = self.browse(order_id['id'])
            if self_id.account_move.id:
                account_move = {}
                for x in orders:
                    if x['data']['name'] == order_id['pos_reference']:
                        account_move = x['data']
                self_id.account_move.l10n_is_third_party_invoice = account_move.get('l10n_is_third_party_invoice', 0)
                self_id.account_move.l10n_is_summary_invoice = account_move.get('l10n_is_summary_invoice', 0)
                self_id.account_move.l10n_is_nominal_invoice = account_move.get('l10n_is_nominal_invoice', 0)
                self_id.account_move.credit_debit_reason = account_move.get('credit_debit_reason', None)
                if len(self_id.refunded_order_ids.account_move.ids) > 1:
                    raise exceptions.ValidationError("only 1 invoice can be returned at a time.")
                self_id.account_move.create_xml_file(pos_refunded_order_id=self_id.refunded_order_ids.account_move.id)
                self.send_to_zatca(self_id.pos_reference)
        return order_ids

    def send_to_zatca(self, pos_reference):
        self = self.sudo().search([('pos_reference', '=', pos_reference)])
        return self.account_move.send_for_reporting(no_xml_generate=1)


   