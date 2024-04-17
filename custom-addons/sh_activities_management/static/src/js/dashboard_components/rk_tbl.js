/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";


// import { Component, useState } from "@odoo/owl";

import { onWillStart, useState, onWillUpdateProps, Component } from "@odoo/owl";

export class RKTable extends Component {

    setup() {
        super.setup();
        alert("....hi....");
        this.action = useService("action");
        this.orm = useService("orm");
        this.state = useState({
            activitytype: {},
        });
        // onWillStart(async () => await this.fetchHierarchy(this.props.record.resId));

        onWillUpdateProps(async (nextProps) => {
            await this.fetchHactivitytype(nextProps);
        });
    }

    async fetchHactivitytype(nextProps) {
        console.log("\n\n\n -fetchHactivitytype--->", nextProps)
        this.state.activitytype = await this.orm.call("activity.dashboard", 
            "sh_get_activity_types", []);
    }
    // this.state.isValidIBAN = await this.orm.call("res.partner.bank", "check_iban", [[], iban]);

    
    // setup() {
    //     this.notificationService = useService("notification");
    // }

    // onDrop(ev) {
    //     const selector = '.account_file_uploader.o_input_file';
    //     // look for the closest uploader Input as it may have a context
    //     let uploadInput = ev.target.closest('.o_drop_area').parentElement.querySelector(selector) || document.querySelector(selector);
    //     let files = ev.dataTransfer ? ev.dataTransfer.files : false;
    //     if (uploadInput && !!files) {
    //         uploadInput.files = ev.dataTransfer.files;
    //         uploadInput.dispatchEvent(new Event("change"));
    //     } else {
    //         this.notificationService.add(
    //             _t("Could not upload files"),
    //             {
    //                 type: "danger",
    //             });
    //     }
    //     this.props.hideZone();
    // }
}
RKTable.props = {
    stage: { type: String, optional: true },
}
RKTable.defaultProps = {
    stage: "",
};
RKTable.template = "sh_activities_management.RKTable";
