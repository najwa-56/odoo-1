/** @odoo-module */

/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */

import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { _t } from "@web/core/l10n/translation";
import { renderToElement } from "@web/core/utils/render";

export class SessionReportButton extends Component {

    static template = "pos_session_report_analysis.SessionReportButton";

    setup() {
        this.pos = usePos();
        this.report = useService("report");
        this.popup = useService("popup"); 
        this.hardwareProxy = useService("hardware_proxy");
    }

    async wk_print_session_summary() {
        const session_id = this.pos.pos_session.id;
        if (!session_id) {
            return;
        }
        const { pos, env, hardwareProxy } = this;
        if (pos.config.iface_print_via_proxy) {
            try {
                const result = await env.services.orm.silent.call(
                    "pos.session",
                    "get_session_report_data",
                    [{ 'session_id': session_id }]
                );
                if (result) {
                    const company = {
                        email: pos.company.email,
                        website: pos.company.website,
                        company_registry: pos.company.company_registry,
                        contact_address: pos.company.partner_id[1],
                        vat: pos.company.vat,
                        phone: pos.company.phone,
                        name: pos.company.name,
                        logo: pos.company_logo_base64,
                    };
                    result['company'] = company;
                    result['widget'] = this;
    
                    const receipt = renderToElement("pos_session_report_analysis.SessionXmlReceipt", result);
                    const printResult = await hardwareProxy.printer.printReceipt(receipt);
                }
            } catch (err) {
                console.error("Error printing session summary:", err);
            }
        } else {
            this.download_session_report(session_id);
        }
    }

    get currentOrder() {
        return this.pos.get_order();
    }

    async download_session_report(session_id) {
        try {
            await this.report.doAction('pos_session_report_analysis.action_wk_report_pos_session_summary', [session_id]);    

        } catch (err) {
            console.error("The report could not be printed:", err);
            this.popup.add(ErrorPopup, {
                'title': _t('The report could not be printed'),
                'body': _t('Check your internet connection and try again.'),
            });
        }
    }

    generate_wrapped_product_name(data) {
        var MAX_LENGTH = 24;
        var wrapped = [];
        var name = data;
        var current_line = "";

        while (name.length > 0) {
            var space_index = name.indexOf(" ");
            if (space_index === -1) {
                space_index = name.length;
            }
            if (current_line.length + space_index > MAX_LENGTH) {
                if (current_line.length) {
                    wrapped.push(current_line);
                }
                current_line = "";
            }
            current_line += name.slice(0, space_index + 1);
            name = name.slice(space_index + 1);
        }

        if (current_line.length) {
            wrapped.push(current_line);
        }
        return wrapped;
    }
}
ProductScreen.addControlButton({
    component: SessionReportButton,
});
