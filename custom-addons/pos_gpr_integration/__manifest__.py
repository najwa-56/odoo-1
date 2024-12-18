# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name"                 :  "Pos Geidea Payment Terminal Integration",
  "summary"              :  """Pos GPR Integration is used to connect/receive payment from Geidea terminal""",
  "category"             :  "Point of Sale",
  "version"              :  "1.0.1",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com",
  "description"          :  """Pos GPR Integration""",
  "depends"              :  [ 'point_of_sale' ],
  "data"                 :  [
                                'views/pos_payment_method_views.xml',
                            ],
  "images"               :  ['static/description/banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "assets"               :  {
                              'point_of_sale._assets_pos': [
                                  "pos_gpr_integration/static/src/lib/*",
                                  "pos_gpr_integration/static/src/app/payment_gpr.js",
                                  "pos_gpr_integration/static/src/app/models.js",
                                  "pos_gpr_integration/static/src/css/pos_gpr.css"
                              ],
                            },
  "auto_install"         :  False,
  "price"                :  499,
  "currency"             :  "USD",
  "pre_init_hook"        :  "pre_init_check",
}
