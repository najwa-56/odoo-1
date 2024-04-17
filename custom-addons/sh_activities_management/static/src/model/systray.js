/** @odoo-module */

import { ActivityMenu } from "@mail/core/web/activity_menu";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(ActivityMenu.prototype, {
    onClickRedirectRecurringActivity(ev) {        
		this.env.services.action.doAction({
			name:_t("Recurrent Activity"),
            type: 'ir.actions.act_window',
            res_model: 'sh.recurring.activities',
            views: [[false, 'list'],[false, 'form']],
        });
    },

});





































// /** @odoo-module **/

// import ActivityMenu from '@mail/js/systray/systray_activity_menu';

// import { _t } from 'web.core';
// const session = require('web.session');
    
// ActivityMenu.include({
//     events: _.extend({}, ActivityMenu.prototype.events, {
//         'click .o_activity_show': '_onrecurrentactivityClick',
//     }),
//     _onrecurrentactivityClick: function (ev) {
//         var self = this;
//         ev.preventDefault();
//         ev.stopPropagation();
//         this.do_action({
//             type: 'ir.actions.act_window',
//             name: _t('Recurrent Activity'),
//             res_model: 'sh.recurring.activities',
//             views: [[false, 'list'],[false, 'form']],
//             target: 'current'
//         });

//     },
//     _onActivityFilterClick: function (ev) {
//         var $el = $(ev.currentTarget);
//         var data = _.extend({}, $el.data());
// 		if (data.res_model === "note.note"){
// 			if (!$el.hasClass("o_note")) {
// 	            var data = _.extend({}, $el.data(), $(ev.target).data());
// 	            if (data.res_model === "note.note" && data.filter === "my") {
// 	                this.do_action({
// 	                    type: 'ir.actions.act_window',
// 	                    name: data.model_name,
// 	                    res_model:  data.res_model,
// 	                    views: [[false, 'kanban'], [false, 'form'], [false, 'list']]
// 	                }, {
// 	                    clear_breadcrumbs: true,
// 	                });
// 	            } else {
// 	                this._super.apply(this, arguments);
// 	            }
// 	        }
// 		}
// 		else if (data.res_model === "crm.lead") {
// 			var data = _.extend({}, $(ev.currentTarget).data(), $(ev.target).data());
//         	var context = {};
//             if (data.filter === 'my') {
//                 context['search_default_activities_overdue'] = 1;
//                 context['search_default_activities_today'] = 1;
//             } else {
//                 context['search_default_activities_' + data.filter] = 1;
//             }
//             // Necessary because activity_ids of mail.activity.mixin has auto_join
//             // So, duplicates are faking the count and "Load more" doesn't show up
//             context['force_search_count'] = 1;
//             this.do_action('crm.crm_lead_action_my_activities', {
//                 additional_context: context,
//                 clear_breadcrumbs: true,
//             });
//         }
//         else if (data.res_model === "calendar.event" && data.filter === "my") {
//             this.do_action('calendar.action_calendar_event', {
//                 additional_context: {
//                     default_mode: 'day',
//                     search_default_mymeetings: 1,
//                 },
//                clear_breadcrumbs: true,
//             });
//         } 
// 		else {
//             var data = _.extend({}, $(ev.currentTarget).data(), $(ev.target).data());
// 	        var context = {};
// 	        if (data.filter === 'my') {
// 	            context['search_default_activities_overdue'] = 1;
// 	            context['search_default_activities_today'] = 1;
// 	        } else {
// 	            context['search_default_activities_' + data.filter] = 1;
// 	        }
// 	        // Necessary because activity_ids of mail.activity.mixin has auto_join
// 	        // So, duplicates are faking the count and "Load more" doesn't show up
// 	        context['force_search_count'] = 1;
	        
// 	        var domain = [['activity_ids.user_id', '=', session.uid],['activity_ids.active','=',true]]
// 	        if (data.domain) {
// 	            domain = domain.concat(data.domain)
// 	        }
	        
// 	        this.do_action({
// 	            type: 'ir.actions.act_window',
// 	            name: data.model_name,
// 	            res_model:  data.res_model,
// 	            views: this._getViewsList(data.res_model),
// 	            search_view_id: [false],
// 	            domain: domain,
// 	            context:context,
// 	        }, {
// 	            clear_breadcrumbs: true,
// 	        });
//         }
//     },
// });

