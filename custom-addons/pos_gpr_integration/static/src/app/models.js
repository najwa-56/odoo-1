/** @odoo-module */

/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */

import { register_payment_method } from "@point_of_sale/app/store/pos_store";
import { Paymentgpr } from "@pos_gpr_integration/app/payment_gpr";

register_payment_method("gpr", Paymentgpr);



// odoo.define('pos_gpr_integration.models', function (require) {
// var models = require('point_of_sale.models');
// var Paymentgpr = require('pos_gpr_integration.payment');
// models.register_payment_method('gpr', Paymentgpr);
// });
