/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { CogMenu } from "@web/search/cog_menu/cog_menu";
import { registry } from "@web/core/registry";

import { useState } from "@odoo/owl";
const cogMenuRegistry = registry.category("cogMenu");
import { onWillStart } from "@odoo/owl";

patch(CogMenu.prototype, {
    setup() { 
        super.setup(); 
        var self = this;
        this.access = useState({removeSpreadsheet: false});  
        onWillStart(async () => {
            let res  = await this.orm.call(
                "access.management",
                "is_spread_sheet_available",
                [1, this?.env?.config?.actionType, this?.env?.config?.actionId]
            )
            if(res){
                this.access.removeSpreadsheet = res;
            }
            this.registryItems = await this._registryItems(); 
        });
    },
    async _registryItems() {
        const items = [];
        for (const item of cogMenuRegistry.getAll()) {
            if(item?.Component?.name === "SpreadsheetCogMenu" && this.access.removeSpreadsheet)
                continue;
            if ("isDisplayed" in item ? await item.isDisplayed(this.env) : true) {
                items.push({
                    Component: item.Component,
                    groupNumber: item.groupNumber,
                    key: item.Component.name,
                });
            }
        }
        return items;
    }
})