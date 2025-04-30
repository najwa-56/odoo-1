from odoo import models, api, SUPERUSER_ID, _
from odoo.tools.translate import _
from odoo.http import request
import ast


class ir_ui_view(models.Model):
    _inherit = 'ir.ui.view'

    def _postprocess_tag_field(self, node, name_manager, node_info):
        super()._postprocess_tag_field(node, name_manager, node_info)
        try:
            hide_field_obj = self.env['hide.field'].sudo()
            hide_fields = hide_field_obj.search(
                        [('model_id.model', '=', name_manager.model._name), ('access_management_id.active', '=', True),
                         ('access_management_id.user_ids', 'in', request.env.uid)])
            
            hide_fields -= hide_fields.filtered(lambda x: x.access_management_id.is_apply_on_without_company == False and self.env.company.id not in x.access_management_id.company_ids.ids)

            if node.tag == 'field' or node.tag == 'label':
                for hide_field in hide_fields:
                    for field_id in hide_field.field_id:
                        # print(node.get('name'), '\n')
                        if (node.tag == 'field' and node.get('name') == field_id.name) or (
                                node.tag == 'label' and 'for' in node.attrib.keys() and node.attrib[
                            'for'] == field_id.name):
                            # if node.tag == 'field':
                            if hide_field.external_link:
                                options_dict = {}
                                if 'widget' in node.attrib.keys():
                                    if node.attrib['widget'] == 'product_configurator' or node.attrib['widget'] == 'many2one_avatar_user':
                                        del node.attrib['widget']
                                        
                                if 'options' in node.attrib.keys():
                                    options_dict = ast.literal_eval(node.attrib['options'])
                                    options_dict.update({"no_edit": True, "no_create": True, "no_open": True})
                                    node.attrib['options'] = str(options_dict)
                                else:
                                    # node.attrib.update({'can_create': 'false', 'can_write': 'false','no_open':'true'})
                                    options_dict.update({'no_create': True, 'no_edit': True,'no_open': True})
                                    node.attrib['options'] = str(options_dict)
                                    
                                # node.attrib.update({'can_create': 'false', 'can_write': 'false','no_open':'true'})
                                    
                            if hide_field.invisible:
                                node_info['column_invisible'] = True
                                node.set('column_invisible', 'True')
                                node_info['invisible'] = True
                                node.set('invisible', '1')
                            if hide_field.readonly:
                                node_info['readonly'] = True
                                node.set('readonly', '1')
                                node.set('force_save', '1')
                            if hide_field.required:
                                node_info['required'] = True
                                node.set('required', '1')

            
        except Exception:
            pass

    def _postprocess_tag_button(self, node, name_manager, node_info):
        # Hide Any Button
        postprocessor = getattr(super(ir_ui_view, self), '_postprocess_tag_button', False)
        if postprocessor:
            super(ir_ui_view, self)._postprocess_tag_button(node, name_manager, node_info)

        hide = None
        hide_button_obj = self.env['hide.view.nodes']
        hide_button_ids = hide_button_obj.sudo().search(
            [('model_id.model', '=', name_manager.model._name), ('access_management_id.active', '=', True),
             ('access_management_id.user_ids', 'in', request.env.uid)])
        
        hide_button_ids -= hide_button_ids.filtered(lambda x: x.access_management_id.is_apply_on_without_company == False and self.env.company.id not in x.access_management_id.company_ids.ids)
        # Filtered with same env user and current model
        btn_store_model_nodes_ids = hide_button_ids.mapped('btn_store_model_nodes_ids')
        # translation_obj = self.env['ir.translation']
        if btn_store_model_nodes_ids:
            for btn in btn_store_model_nodes_ids:
                if btn.attribute_name == node.get('name') or btn.attribute_string == node.get('string'):
                    hide = [btn]
                    break
                    
        if hide:
            node.set('invisible', '1')
            if 'attrs' in node.attrib.keys() and node.attrib['attrs']:
                del node.attrib['attrs']
            node_info['invisible'] = True

        return None

    def _postprocess_tag_page(self, node, name_manager, node_info):
        # Hide Any Notebook Page
        postprocessor = getattr(super(ir_ui_view, self), '_postprocess_tag_page', False)
        if postprocessor:
            super(ir_ui_view, self)._postprocess_tag_page(node, name_manager, node_info)

        hide = None
        hide_tab_obj = self.env['hide.view.nodes']
        hide_tab_ids = hide_tab_obj.sudo().search([('model_id.model', '=', name_manager.model._name),
                                                   ('access_management_id.active', '=', True),
                                                   ('access_management_id.user_ids', 'in', request.env.uid)])
        
        hide_tab_ids -= hide_tab_ids.filtered(lambda x: x.access_management_id.is_apply_on_without_company == False and self.env.company.id not in x.access_management_id.company_ids.ids)
        page_store_model_nodes_ids = hide_tab_ids.mapped('page_store_model_nodes_ids')
        if page_store_model_nodes_ids:

            for tab in page_store_model_nodes_ids:
                attribute_string = tab.attribute_string
                if tab.lang_code != self.env.lang:
                    field = self.env['ir.ui.view']._fields['arch_db']
                    translation_dictionary = field.get_translation_dictionary(
                        self.with_context(lang=tab.lang_code).arch_db,
                        {self.env.lang: self.with_context(lang=self.env.lang)['arch_db']})
                    attribute_string = translation_dictionary[attribute_string][self.env.lang]
                if attribute_string == node.get('string'):
                    hide = [tab]
                    break
                    
        if hide:
            node.set('invisible', '1')
            if 'attrs' in node.attrib.keys() and node.attrib['attrs']:
                del node.attrib['attrs']

            node_info['invisible'] = True

        return None

    def _postprocess_tag_a(self, node, name_manager, node_info):
        # Hide Any Notebook Page
        postprocessor = getattr(super(ir_ui_view, self), '_postprocess_tag_a', False)
        if postprocessor:
            super(ir_ui_view, self)._postprocess_tag_page(node, name_manager, node_info)

        hide = None
        hide_tab_obj = self.env['hide.view.nodes']
        hide_tab_ids = hide_tab_obj.sudo().search([('model_id.model', '=', name_manager.model._name),
                                                   ('access_management_id.active', '=', True),
                                                   ('access_management_id.user_ids', 'in', request.env.uid)])
        
        hide_tab_ids -= hide_tab_ids.filtered(lambda x: x.access_management_id.is_apply_on_without_company == False and self.env.company.id not in x.access_management_id.company_ids.ids)
        link_store_model_nodes_ids = hide_tab_ids.mapped('link_store_model_nodes_ids')
        if link_store_model_nodes_ids:
            for link in link_store_model_nodes_ids:
                
                if _(link.attribute_name) == node.get('name'):
                    hide = [link]
                    break
                      
        if hide:
            node.set('invisible', '1')
            if 'attrs' in node.attrib.keys() and node.attrib['attrs']:
                del node.attrib['attrs']

            node_info['invisible'] = True

        return None

    def _postprocess_tag_div(self, node, name_manager, node_info):
        # Hide Any Notebook Page
        postprocessor = getattr(super(ir_ui_view, self), '_postprocess_tag_div', False)
        if postprocessor:
            super(ir_ui_view, self)._postprocess_tag_page(node, name_manager, node_info)

        hide_button_obj = self.env['hide.view.nodes']
        setting_tabs = hide_button_obj.sudo().search([('model_id.model', '=', name_manager.model._name),
                                                       ('access_management_id.active', '=', True),
                                                       ('access_management_id.user_ids', 'in', request.env.uid)])
        
        setting_tabs -= setting_tabs.filtered(lambda x: x.access_management_id.is_apply_on_without_company == False and self.env.company.id not in x.access_management_id.company_ids.ids)

        if name_manager.model._name == 'res.config.settings' and node.tag == 'app' and node.get('string'):
            for setting_tab in setting_tabs.mapped('page_store_model_nodes_ids'):
                attribute_string = setting_tab.attribute_string
                if setting_tab.lang_code != self.env.lang:
                    field = self.env['ir.ui.view']._fields['arch_db']
                    translation_dictionary = field.get_translation_dictionary(
                        self.with_context(lang=setting_tab.lang_code).arch_db,
                        {self.env.lang: self.with_context(lang=self.env.lang)['arch_db']})
                    attribute_string = translation_dictionary[attribute_string][self.env.lang]
                if node.get('data-key') == setting_tab.attribute_name:
                    # if node.get('string') == attribute_string and node.get('data-key') == setting_tab.attribute_name:
                    node_info['invisible'] = True
                    node.set('invisible', '1')

        return None

    def _postprocess_tag_filter(self, node, name_manager, node_info):
        # Hide Any Notebook Page
        postprocessor = getattr(super(ir_ui_view, self), '_postprocess_tag_filter', False)
        if postprocessor:
            super(ir_ui_view, self)._postprocess_tag_page(node, name_manager, node_info)
        # if node.tag == 'group':
        #     pass
        if node.tag == 'filter' or node.tag == 'group':
            hide_filter_group_obj = self.env['hide.filters.groups'].sudo().search(
                [('model_id.model', '=', name_manager.model._name), ('access_management_id.active', '=', True),
                 ('access_management_id.user_ids', 'in', request.env.uid)])
            
            hide_filter_group_obj -= hide_filter_group_obj.filtered(lambda x: x.access_management_id.is_apply_on_without_company == False and self.env.company.id not in x.access_management_id.company_ids.ids)

            for hide_field_obj in hide_filter_group_obj:
                for hide_filter in hide_field_obj.filters_store_model_nodes_ids.mapped('attribute_name'):
                    if node.tag == 'filter' and hide_filter == node.get('name', False):
                        node_info['invisible'] = True
                        node.set('invisible', '1')
            for hide_field_obj in hide_filter_group_obj:
                for hide_filter in hide_field_obj.groups_store_model_nodes_ids.mapped('attribute_name'):
                    if hide_filter == node.get('name', False):
                        node_info['invisible'] = True
                        node.set('invisible', '1')
        return None
        
    def _postprocess_tag_label(self, node, name_manager, node_info):
        postprocessor = getattr(super(ir_ui_view, self), '_postprocess_tag_label', False)
        hide_field_obj = self.env['hide.field'].sudo()
        if postprocessor:
            super(ir_ui_view, self)._postprocess_tag_label(node, name_manager, node_info)
            if node.get('for'):
                hide_lable = hide_field_obj.search([('model_id.model','=',name_manager.model._name),
                                                    ('access_management_id.active','=',True),
                                                    ('access_management_id.user_ids','in',request.env.uid)])
                
                hide_lable -= hide_lable.filtered(lambda x: x.access_management_id.is_apply_on_without_company == False and self.env.company.id not in x.access_management_id.company_ids.ids)

                for hide_field in hide_lable:
                    for field_id in hide_field.field_id:
                        if node.get('for') == field_id.name and node.get('string') == field_id.field_description:
                            node_info['invisible'] = True
                            node.set('invisible', '1')

    # def _get_view(self, view_id=None, view_type='form', **options):
    #     arch, view = super()._get_view(view_id, view_type, **options)
    #     access_management_obj = self.env['access.management']
    #     # cids = request.httprequest.cookies.get('cids') and request.httprequest.cookies.get('cids').split(',')[0] or request.env.company.id
    #     readonly_access_id = access_management_obj.sudo().search(
    #         [('company_ids', 'in', self.env.company.id), ('active', '=', True), ('user_ids', 'in', self.env.user.id),
    #          ('readonly', '=', True)])

    #     access_recs = self.env['access.domain.ah'].sudo().search(
    #         [('access_management_id.user_ids', 'in', self.env.user.id), ('access_management_id.active', '=', True),
    #          ('model_id.model', '=', self._name)])
        
    #     access_recs -= access_recs.filtered(lambda x: x.access_management_id.is_apply_on_without_company == False and self.env.company.id not in x.access_management_id.company_ids.ids)

    #     access_model_recs = self.env['remove.action'].sudo().search(
    #         [('access_management_id.user_ids', 'in', self.env.user.id),
    #          ('access_management_id.active', '=', True),
    #          ('model_id.model', '=', self._name)])
        
    #     access_model_recs -= access_model_recs.filtered(lambda x: x.access_management_id.is_apply_on_without_company == False and self.env.company.id not in x.access_management_id.company_ids.ids)

    #     if view_type == 'form':
    #         access_management_id = access_management_obj.sudo().search([
    #                                                              ('active', '=', True),
    #                                                              ('user_ids', 'in', self.env.user.id),
    #                                                              ('hide_chatter', '=', True)],
    #                                                             limit=1)
    #         if access_management_id and access_management_id.is_apply_on_without_company:
    #             for div in arch.xpath("//div[@class='oe_chatter']"):
    #                 div.getparent().remove(div)
    #         elif self.env.company in access_management_id.company_ids:
    #             for div in arch.xpath("//div[@class='oe_chatter']"):
    #                 div.getparent().remove(div)
    #         else:
    #             hide_chatter_id = self.env['hide.chatter'].sudo().search([('access_management_id.active', '=', True),
    #                                                 ('access_management_id.user_ids', 'in', self.env.user.id),
    #                                                 ('model_id.model', '=', self._name),
    #                                                 ('hide_chatter', '=', True)],
    #                                                limit=1)
                
    #             if hide_chatter_id and hide_chatter_id.access_management_id.is_apply_on_without_company:
    #                 for chatter_path in arch.xpath("//div[@class='oe_chatter']"):
    #                     chatter_path.getparent().remove(chatter_path)

    #             elif self.env.company in hide_chatter_id.access_management_id.company_ids:
    #                 for chatter_path in arch.xpath("//div[@class='oe_chatter']"):
    #                     chatter_path.getparent().remove(chatter_path)

    #     if view_type in ['kanban', 'tree']:
    #         restrict_import = access_management_obj.sudo().search([('company_ids', 'in', self.env.company.id),
    #                                                         ('active', '=', True),
    #                                                         ('user_ids', 'in', self.env.user.id),
    #                                                         ('hide_import', '=', True)], limit=1)
            

    #         if access_model_recs.filtered(lambda x: x.restrict_import) or restrict_import and restrict_import.is_apply_on_without_company:
    #             doc = arch
    #             doc.attrib.update({'import': 'false'})
    #             arch = doc

    #         restrict_export = access_management_obj.sudo().search([
    #                                                         ('active', '=', True),
    #                                                         ('user_ids', 'in', self.env.user.id),
    #                                                         ('hide_export', '=', True)], limit=1)
    #         restrict_export = restrict_export.filtered(lambda x: x.is_apply_on_without_company or self.env.company.id in x.company_ids.ids)

    #         if access_model_recs.filtered(lambda x: x.restrict_export) or restrict_export:
    #             doc = arch
    #             doc.attrib.update({'export_xlsx': 'false'})
    #             arch = doc

    #     if readonly_access_id:
    #         if view_type == 'form':
    #             arch.attrib.update({'create': 'false', 'delete': 'false', 'edit': 'false'})

    #         if view_type == 'tree':
    #             arch.attrib.update({'create': 'false', 'delete': 'false', 'edit': 'false'})

    #         if view_type == 'kanban':
    #             arch.attrib.update({'create': 'false', 'delete': 'false', 'edit': 'false'})

    #     else:

    #         if access_model_recs:
    #             delete = 'true'
    #             edit = 'true'
    #             create = 'true'
    #             for access_model in access_model_recs:
    #                 if access_model.restrict_create:
    #                     create = 'false'
    #                 if access_model.restrict_edit:
    #                     edit = 'false'
    #                 if access_model.restrict_delete:
    #                     delete = 'false'

    #             if view_type == 'form':
    #                 arch.attrib.update({'create': create, 'delete': delete, 'edit': edit})

    #             if view_type == 'tree':
    #                 arch.attrib.update({'create': create, 'delete': delete, 'edit': edit})

    #             if view_type == 'kanban':
    #                 arch.attrib.update({'create': create, 'delete': delete, 'edit': edit})

    #         if access_recs:
    #             delete = 'false'
    #             edit = 'false'
    #             create = 'false'
    #             for access_rec in access_recs:
    #                 if access_rec.create_right:
    #                     create = 'true'
    #                 if access_rec.write_right:
    #                     edit = 'true'
    #                 if access_rec.delete_right:
    #                     delete = 'true'

    #             if view_type == 'form':
    #                 arch.attrib.update({'create': create, 'delete': delete, 'edit': edit})

    #             if view_type == 'tree':
    #                 arch.attrib.update({'create': create, 'delete': delete, 'edit': edit})

    #             if view_type == 'kanban':
    #                 arch.attrib.update({'create': create, 'delete': delete, 'edit': edit})

    #     return arch, view
            

    # @api.model
    # def _get_view(self, view_id=None, view_type='form', **options):
    #     arch, view = super()._get_view(view_id, view_type, **options)

    #     return arch, view