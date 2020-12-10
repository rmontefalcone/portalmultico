# -*- encoding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging

import pytz

from odoo import models
from odoo.http import request

logger = logging.getLogger(__name__)


class Http(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _add_dispatch_parameters(cls, func):

        # Force website with query string paramater, typically set from website selector in frontend navbar
        force_website_id = request.httprequest.args.get('fw')
        if (force_website_id and request.session.get('force_website_id') != force_website_id and
                request.env.user.has_group('website.group_multi_website') and
                request.env.user.has_group('website.group_website_publisher')):
            request.env['website']._force_website(request.httprequest.args.get('fw'))

        context = {}
        if not request.context.get('tz'):
            context['tz'] = request.session.get('geoip', {}).get('time_zone')
            try:
                pytz.timezone(context['tz'] or '')
            except pytz.UnknownTimeZoneError:
                context.pop('tz')

        request.website = request.env[
            'website'].get_current_website()  # can use `request.env` since auth methods are called
        context['website_id'] = request.website.id
        # This is mainly to avoid access errors in website controllers where there is no
        # context (eg: /shop), and it's not going to propagate to the global context of the tab
        # If the company of the website is not in the allowed companies of the user, set the main
        # company of the user.

        # CUSTOM ADD: Si usuario portal tomar sus compañías permitidas y no la del Website o la del Usuario
        is_portal_user = request.env.user != request.website.user_id and request.env.user.share
        if is_portal_user:
            context['allowed_company_ids'] = request.env.user.company_ids.ids
        elif request.website.company_id in request.env.user.company_ids:
            context['allowed_company_ids'] = request.website.company_id.ids
        else:
            context['allowed_company_ids'] = request.env.user.company_id.ids

        # modify bound context
        request.context = dict(request.context, **context)

        super(Http, cls)._add_dispatch_parameters(func)

        if request.routing_iteration == 1:
            request.website = request.website.with_context(request.context)
