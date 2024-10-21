# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from collections import defaultdict
from datetime import datetime
from functools import partial
from itertools import groupby
from markupsafe import Markup
from random import randrange

import base64
import logging
import psycopg2
import pytz
import re

from odoo import api, fields, models, tools, _
from odoo.tools import float_is_zero, float_round, float_repr, float_compare
from odoo.exceptions import ValidationError, UserError
from odoo.osv.expression import AND

_logger = logging.getLogger(__name__)

class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def search_paid_order_ids(self, config_id, domain, limit, offset):
        """Search for 'paid' orders that satisfy the given domain, limit and offset."""
        default_domain = [('state', '!=', 'draft'), ('state', '!=', 'cancel')]
        if domain == []:
            # ['config_id', '=', config_id]
            real_domain = AND([[], default_domain])
        else:
            real_domain = AND([domain, default_domain])
        orders = self.search(real_domain, limit=limit, offset=offset)
        # We clean here the orders that does not have the same currency.
        # As we cannot use currency_id in the domain (because it is not a stored field),
        # we must do it after the search.
        pos_config = self.env['pos.config'].browse(config_id)

        # orders = orders.filtered(lambda order: order.currency_id == pos_config.currency_id)

        orderlines = self.env['pos.order.line'].search(['|', ('refunded_orderline_id.order_id', 'in', orders.ids), ('order_id', 'in', orders.ids)])

        # We will return to the frontend the ids and the date of their last modification
        # so that it can compare to the last time it fetched the orders and can ask to fetch
        # orders that are not up-to-date.
        # The date of their last modification is either the last time one of its orderline has changed,
        # or the last time a refunded orderline related to it has changed.
        orders_info = defaultdict(lambda: datetime.min)
        for orderline in orderlines:
            key_order = orderline.order_id.id if orderline.order_id in orders \
                            else orderline.refunded_orderline_id.order_id.id
            if orders_info[key_order] < orderline.write_date:
                orders_info[key_order] = orderline.write_date
        totalCount = self.search_count(real_domain)
        return {'ordersInfo': list(orders_info.items())[::-1], 'totalCount': totalCount}

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
                #wirte pos refeernce in account move so that we get barcode for return
                self_id.account_move.write({'pos_reference':self_id.pos_reference})

                # self.send_to_zatca(self_id.pos_reference)
        return order_ids

    def send_to_zatca(self, pos_reference):
        self = self.sudo().search([('pos_reference', '=', pos_reference)])
        return self.account_move.send_for_reporting(no_xml_generate=1)


   

    @api.model
    def get_qr_code(self):
        def get_qr_encoding(tag, field):
            company_name_byte_array = field.encode('UTF-8')
            company_name_tag_encoding = tag.to_bytes(length=1, byteorder='big')
            company_name_length_encoding = len(company_name_byte_array).to_bytes(length=1, byteorder='big')
            return company_name_tag_encoding + company_name_length_encoding + company_name_byte_array
        qr_code_str = ''
        seller_name_enc = get_qr_encoding(1, self.company_id.display_name)
        company_vat_enc = get_qr_encoding(2, self.company_id.vat or '')
        date_order = fields.Datetime.context_timestamp(self.with_context(tz='Asia/Riyadh'), self.date_order)
        timestamp_enc = get_qr_encoding(3, str(date_order.isoformat()))
        invoice_total_enc = get_qr_encoding(4, str(round(abs(self.amount_total),2)))
        total_vat_enc = get_qr_encoding(5, str(round(abs(self.amount_tax),2)))
        str_to_encode = seller_name_enc + company_vat_enc + timestamp_enc + invoice_total_enc + total_vat_enc
        qr_code_str = base64.b64encode(str_to_encode).decode('UTF-8')
        return qr_code_str