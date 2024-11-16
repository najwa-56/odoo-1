/** @odoo-module **/

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
const userMenuRegistry = registry.category("user_menuitems");

userMenuRegistry.add('print_report_preview',  function (env) {
    return {
        type: "item",
        id: "print_report_preview",
        description: _t("Report Preview"),
        callback: async function () {
            const actionDescription = await env.services.orm.call("res.users", "action_get_print_report_preview");
            actionDescription.res_id = env.services.user.userId;
            env.services.action.doAction(actionDescription);
        },
        sequence: 5,
    };
}, { force: true });
