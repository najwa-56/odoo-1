# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

import json
import logging
import pprint
import random
import requests
import string
from werkzeug.exceptions import Forbidden

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    def _get_payment_terminal_selection(self):
        return super(PosPaymentMethod, self)._get_payment_terminal_selection() + [('gpr', 'Odoo Payments by gpr')]

    gpr_api_key = fields.Char(string="Com Port Name")
    gpr_terminal_identifier = fields.Char(string="Com Port")
    gpr_test_mode = fields.Boolean(help='Run transactions in the test environment.')

class PosPayment(models.Model):
    _inherit = "pos.payment"

    gpr_data = fields.Text(string="GPR Data")
    TransactionResponseEnglish = fields.Char("Transaction Response")
    PrimaryAccountNumber = fields.Char("PrimaryAccountNumber")
    TransactionAmount = fields.Char("TransactionAmount")
    TransactionDateTime = fields.Char("TransactionDateTime")
    TransactionAuthCode = fields.Char("TransactionAuthCode")
    CardScheme = fields.Char("CardScheme")
    POSEntryMode = fields.Char("POSEntryMode")
    CardAcceptorTerminalId = fields.Char("CardAcceptorTerminalId")
    RetrievalReferenceNumber = fields.Char("RetrievalReferenceNumber")
    CardAcceptorIdCode = fields.Char("CardAcceptorIdCode")

class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def _payment_fields(self, order, ui_paymentline):
        args = super(PosOrder, self)._payment_fields(order, ui_paymentline)
        if ui_paymentline.get('gpr_data'):
            data = eval(ui_paymentline.get('gpr_data'))
            args.update({
                'TransactionResponseEnglish': data.get("TransactionResponseEnglish"),
                'PrimaryAccountNumber' : data.get("PrimaryAccountNumber"),
                'TransactionAmount' : data.get("TransactionAmount"),
                'TransactionDateTime' : data.get("TransactionDateTime"),
                'TransactionAuthCode' : data.get("TransactionAuthCode"),
                'CardScheme' : '',
                'POSEntryMode' : data.get("POSEntryMode"),
                'CardAcceptorTerminalId' : data.get("CardAcceptorTerminalId"),
                'RetrievalReferenceNumber' : data.get("RetrievalReferenceNumber"),
                'CardAcceptorIdCode' : data.get("CardAcceptorIdCode"),
                'gpr_data':data
            })
        return args
