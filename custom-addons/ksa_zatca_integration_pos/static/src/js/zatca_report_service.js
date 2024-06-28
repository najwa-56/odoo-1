///** @odoo-module **/
//
//import { registry } from "@web/core/registry";
//import { browser } from "@web/core/browser/browser";
//import { EventBus } from "@odoo/owl";
//
//export class ZatcaReport {
//    static serviceDependencies = []
//    constructor(parser) {
//        this.parser = parser;
//    }
//
//    async get_report(name) {
//        let response = await this.orm.call('pos.order', 'get_simplified_zatca_report', [[], name]);
//        if (response)
//            response = $($(response)).find('.pos-receipt').parent().html()
//        return response
//    }
//}
//
//export const ZatcaReportService = {
//    dependencies: [],
//    async start(env, deps) {
//        let ZatcaReport = null;
//         ZatcaReport = new ZatcaReport('test');
//        return ZatcaReport;
//    },
//};
//
//registry.category("services").add("zatca_report_service", ZatcaReportService);
