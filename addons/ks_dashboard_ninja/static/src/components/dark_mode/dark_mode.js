/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart } from "@odoo/owl";
import { loadBundle } from '@web/core/assets';
import { cookie } from "@web/core/browser/cookie";
import { browser } from "@web/core/browser/browser";

export class DNDarkMode extends Component {
    static template = "ks_dashboard_ninja.dn_dark_mode"
    setup() {
        this.dn_color_scheme = (cookie.get("configured_color_scheme") === "dark" || cookie.get("color_scheme") === "dark")
                                        ? "dark" : (cookie.get("dn_color_scheme") || "light");
        onWillStart( () => {
            if(this.dn_color_scheme === 'dark'){
                loadBundle("ks_dashboard_ninja.dn_dark_mode");
            }
        })
    }

    set_cookie(scheme){
        cookie.set("dn_color_scheme", scheme);
    }

    apply_dark_mode(scheme){
        this.set_cookie(scheme === 'light' ? 'dark' : 'light');
        this.reload();
    }

    reload() {
        browser.location.reload();
    }
}



//registry.category("systray").add("DNDarkMode", { Component: DNDarkMode }, { sequence: 400 });



