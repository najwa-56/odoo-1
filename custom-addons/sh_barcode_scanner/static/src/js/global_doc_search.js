/* @odoo-module */

import { Component, useState, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { _t } from "@web/core/l10n/translation";

export class ShBarcodeScannerSearchDocument extends Component {
    static template = "sh_barcode_scanner.GlobalDocSearch";
    static components = { Dropdown };
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.ui = useState(useService("ui"));
        this.action = useService("action");
        this.selectDocument = useRef("selectDocument");
        this.notification = useService("notification");
    }

    async _onChangeBarcode(ev) {
        let barcode = ev.target.value;
        const result =await this.orm.call("sh_barcode_scanner.search.document", "search_document",[barcode ,this.selectDocument.el.value]);
        if (result.action){
            this.action.doAction(result.action);
        }
        else{
            this.notification.add(_t("Document not found for the barcode: " + barcode), {
                title: _t("Global Search"),
                type: "danger",
            });
        }
        ev.target.value = "";
    }
}
export const ShGlobalSearchBarcodeService = {
    start(env) {
        let isEnabled = false;
        return {
            async check() {
                isEnabled = await env.services.orm.call("sh_barcode_scanner.search.document", "has_global_search_enabled");
            },
            get isEnabled() {
                return isEnabled;
            }
        }
    }
}

registry.category("services").add("shglobalsearchbarcode", ShGlobalSearchBarcodeService);

export const systrayItem = {
    Component: ShBarcodeScannerSearchDocument,
    isDisplayed: function (env) {
        const global_search_barcode = env.services.shglobalsearchbarcode
        global_search_barcode.check()
        return global_search_barcode.isEnabled
    }
};

registry.category("systray").add("ShBarcodeScannerSearchDocumentSystrayItem", systrayItem, { sequence: 1 });
