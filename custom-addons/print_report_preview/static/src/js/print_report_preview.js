/** @odoo-module **/

import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { _t } from "@web/core/l10n/translation";
import { ReportPreviewDialog } from "./report_preview_dialog"

let wkhtmltopdfStateProm;
const link = '<br><br><a href="http://wkhtmltopdf.org/" target="_blank">wkhtmltopdf.org</a>';

function _getReportUrl(action, type) {
    let url = `/report/${type}/${action.report_name}`;
    const actionContext = action.context || {};
    if (action.data && JSON.stringify(action.data) !== "{}") {
        const options = encodeURIComponent(JSON.stringify(action.data));
        const context = encodeURIComponent(JSON.stringify(actionContext));
        url += `?options=${options}&context=${context}`;
    } else {
        if (actionContext.active_ids) {
            url += `/${actionContext.active_ids.join(",")}`;
        }
        if (type === "html") {
            const context = encodeURIComponent(JSON.stringify(env.services.user.context));
            url += `?context=${context}`;
        }
    }
    return url;
}

registry.category("ir.actions.report handlers").add("print_report_preview", async function (action, options, env) {
    if (action.report_type === "qweb-pdf" && env.services.menu !== undefined) {
        if(session.report_preview || session.report_automatic_printing){
            if (!wkhtmltopdfStateProm) {
                wkhtmltopdfStateProm = env.services.rpc("/report/check_wkhtmltopdf");
            }
            const state = await wkhtmltopdfStateProm;
            const WKHTMLTOPDF_MESSAGES = {
                broken:
                    _t(
                        "Your installation of Wkhtmltopdf seems to be broken. The report will be shown " +
                            "in html."
                    ) + link,
                install:
                    _t(
                        "Unable to find Wkhtmltopdf on this system. The report will be shown in " + "html."
                    ) + link,
                upgrade:
                    _t(
                        "You should upgrade your version of Wkhtmltopdf to at least 0.12.0 in order to " +
                            "get a correct display of headers and footers as well as support for " +
                            "table-breaking between pages."
                    ) + link,
                workers: _t(
                    "You need to start Odoo with at least two workers to print a pdf version of " +
                        "the reports."
                ),
            };
            if (state in WKHTMLTOPDF_MESSAGES) {
                env.services.notification.add(WKHTMLTOPDF_MESSAGES[state], {
                    sticky: true,
                    title: _t("Report"),
                });
            }
            if (state === "upgrade" || state === "ok") {
                const type = "pdf";
                const reportUrl = _getReportUrl(action, type);
                const title = action.name;
                
                if(session.report_preview){
                    env.services.dialog.add(ReportPreviewDialog, { 
                        title:title,
                        reportUrl:reportUrl,
                    });
                }
                if (session.report_automatic_printing) {                   
                    try {
                        var pdf = window.open(reportUrl);
                        pdf.print();    
                    }
                    catch(err) {
                        var ERR_MESSAGES = _t("Please allow pop upin your browser to preview report in another tab.");
                        env.services.notification.add(ERR_MESSAGES, {
                                sticky: true,
                                title: _t("Warning"),    
                            }
                        );
                    }
                }
                return true;
            }
        }
    }
});
