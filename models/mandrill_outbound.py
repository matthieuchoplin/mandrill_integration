# -*- coding: utf-8 -*-
##############################################################################
#
#    This module copyright :
#        (c) 2015 Endika Iglesias <endika2@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields
import datetime
import mandrill


class MandrillOutbound(models.Model):
    _name = "mandrill.outbound"
    _description = "Mandrill Outbound"

    name = fields.Char(
        "Subject email", size=200, readonly=True, required=True)
    email_id = fields.Char(
        "Mandrill internal id", size=200, readonly=True, required=True)
    opens = fields.Integer(
        "Opens", size=10, default=0, readonly=True, required=True)
    clicks = fields.Integer(
        "Clicks", size=10, default=0, readonly=True, required=True)
    sender = fields.Char("From", size=200, readonly=True, required=False)
    to = fields.Char("To", size=1000, readonly=True, required=False)
    state = fields.Char("State", size=50, readonly=True, required=False)
    date = fields.Datetime('Register date', readonly=True, required=True)
    content = fields.Char("Content", size=5000, readonly=True, required=False)

    def _api_key(self, cr, uid, ids, context=None):
        config_pool = self.pool.get('ir.config_parameter')
        api_key = config_pool.get_param(cr,
                                        uid,
                                        'mandrill_integration.api_key',
                                        default=False,
                                        context=context)
        if api_key is False or len(api_key) <= 0:
            return False
        return api_key

    def call_cron_mandrill_outbound(self, cr, uid, context=None):
        api_key = self._api_key(cr, uid, [],
                                context=context)
        if api_key is False:
            return False

        mandrill_out = self.pool['mandrill.outbound']
        date_now = datetime.datetime.now().strftime("%Y-%m-%d")
        year_now = datetime.datetime.now().strftime("%Y")
        date_rest = datetime.datetime.now().strftime("-%m-%d")
        date_init = str(int(year_now) - 1) + date_rest
        mandrill_client = mandrill.Mandrill(api_key)
        email_list = mandrill_client.messages.search(query='*',
                                                     date_from=date_init,
                                                     date_to=date_now)
        masc = "%Y-%m-%d %H:%M:%S"
        date_now = datetime.datetime.now().strftime(masc)

        for email in email_list:
            mandrill_ids = mandrill_out.search(cr, uid,
                                               [('email_id', '=', email['_id'])
                                                ], context=context)

            opens = int(email['opens'])
            clicks = int(email['clicks'])
            mandrill_map = {"name": email['subject'],
                            "email_id": email['_id'],
                            "opens": opens if opens > 0 else 0,
                            "clicks": clicks if clicks > 0 else 0,
                            "sender": email['sender'],
                            "to": email['email'],
                            "state": email['state'],
                            "date": date_now,
                            }

            if not mandrill_ids:
                try:
                    e_cont = mandrill_client.messages.content(id=email['_id'])
                    mandrill_map['content'] = e_cont['text']
                except mandrill.Error:
                    mandrill_map['content'] = "No available"

                mandrill_out.create(cr, uid,
                                    mandrill_map,
                                    context=context)
                continue

            del mandrill_map['date']
            mandrill_out.write(cr, uid, mandrill_ids,
                               mandrill_map,
                               context=context)
