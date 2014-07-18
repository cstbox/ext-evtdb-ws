#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of CSTBox.
#
# CSTBox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# CSTBox is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with CSTBox.  If not, see <http://www.gnu.org/licenses/>.

""" Events Database access service """

__author__ = 'Eric PASCUAL - CSTB (eric.pascual@cstb.fr)'

from tornado.web import HTTPError

from pycstbox import log, evtdao
from pycstbox.events import DataKeys
from pycstbox.webservices.wsapp import WSHandler


def _init_(logger=None, settings=None):
    """ Module init function, called by the application framework during the
    services discovery process.

    settings expected content:
     - dao : the name of the DAO to be used (defaulted to "fsys")
    """

    # inject the (provided or created) logger in handlers default initialize parameters
    _handlers_initparms['logger'] = logger if logger else log.getLogger('svc.hello')

    # same for the DAO, based on the configuration from settings if available
    dao_name = settings.get('dao', 'fsys')
    try:
        dao = evtdao.get_dao(dao_name)
    except Exception as e:
        raise ValueError("cannot access to DAO '%s' (%s)" % (dao_name, e))
    else:
        _handlers_initparms['dao'] = dao


class BaseHandler(WSHandler):
    """ Root class for requests handlers.

    It takes care of storing the DAO instance configured when initializing the service module.
    """
    def initialize(self, logger=None, dao=None, **kwargs):
        super(BaseHandler, self).initialize(logger, **kwargs)
        self._dao = dao


class GetAvailableDaysHandler(BaseHandler):
    """ Retrieves the list of days for which data are available

    HTTP request arguments:
        m : the month number (1 <= m <= 12)
        y : the year (full number with centuries)
    """
    def do_get(self):
        try:
            month = (int(self.get_argument("y")), int(self.get_argument("m")))
        except HTTPError:
            month = None

        days = []
        for day in self._dao.get_available_days(month):
            days.append(day.strftime('%Y/%m/%d'))

        self.write({'days': days})


class GetEventsHandler(BaseHandler):
    """ Retrieves the list of events available for a given day

    HTTP request arguments:
        d : the day
            (format : SQL date by default, but '/' separator
            are accepted too)

    """
    def get(self):
        day = self.get_argument("d").replace('/', '-')

        _events = []
        for event in self._dao.get_events_for_day(day):
            ts, var_type, var_name, data = event
            value = data.get(DataKeys.VALUE, '')
            units = data.get(DataKeys.UNITS, '')

            _events.append((ts.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                            var_type, var_name, value, units))

        self.write({'events': _events})

_handlers_initparms = {}

handlers = [
    (r"/days", GetAvailableDaysHandler, _handlers_initparms),
    (r"/events", GetEventsHandler, _handlers_initparms),
]
