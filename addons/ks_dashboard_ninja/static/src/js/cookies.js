/** @odoo-module **/

import { isMobileOS } from "@web/core/browser/feature_detection";

export  const setObjectInSession = (name, object) => {
    let jsonString = JSON.stringify(object);
    !isMobileOS() ? sessionStorage.setItem(name, jsonString) : '';
}

export const getObjectFromSession = (name) => {
    let jsonString = sessionStorage.getItem(name);
    return !isMobileOS() && jsonString ? JSON.parse(jsonString) : null;
}
export const eraseSessionItem = (name) => {
    sessionStorage.removeItem(name)
}

