/** @odoo-module */
import { ajax } from '@web/core/ajax';

export async function fetchUserGroups() {
    try {
        const userGroups = await ajax.jsonRpc('/api/user_groups', 'call', {});
        return userGroups;
    } catch (error) {
        console.error('Failed to fetch user groups:', error);
        return [];
    }
}