/** @odoo-module **/


export  const setObjectInSession = (name, object) => {
    let jsonString = JSON.stringify(object);
    sessionStorage.setItem(name, jsonString);
}

export const getObjectFromSession = (name) => {
    let jsonString = sessionStorage.getItem(name);
    return jsonString ? JSON.parse(jsonString) : null;
}
export const eraseSessionItem = (name) => {
    sessionStorage.removeItem(name);
}

