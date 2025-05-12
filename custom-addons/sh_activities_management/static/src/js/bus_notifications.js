/* @odoo-module */

import { simpleNotificationService } from "@bus/simple_notification_service";
import { patch } from "@web/core/utils/patch";
import { markup } from "@odoo/owl";

patch(simpleNotificationService,{
    start(env, { bus_service, notification: notificationService }) {
        bus_service.subscribe("simple_notification", ({ message, sticky, title, type }) => {            
            notificationService.add(markup(message), { sticky, title, type });
        });
        bus_service.start();
    },
})
