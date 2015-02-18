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

import dateutil.parser

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
        """
        :param logger logger: message logger
        :param pycstbox.evtdao.base.AbstractDAO dao: DAO used to access the data
        """
        super(BaseHandler, self).initialize(logger, **kwargs)
        self._dao = dao


class GetAvailableDaysHandler(BaseHandler):
    """ Retrieves the list of days for which data are available

    HTTP request arguments:
        m : the month number (1 <= m <= 12)
        y : the year (full number with centuries)
    """
    def do_get(self):

        month = (int(self.get_argument("y")), int(self.get_argument("m")))
        days = []
        for day in self._dao.get_available_days(month):
            days.append(day.strftime('%Y/%m/%d'))

        self.write({'days': days})


class GetDayEventsHandler(BaseHandler):
    """ Retrieves the list of events available for a given day

    HTTP request arguments:
        d : the day (format : "YYYY-MM-DD" or "YYYY/MM/DD")

    """
    def get(self):
        day = self.get_argument("d").replace('/', '-')

        _events = []
        for event in self._dao.get_events_for_day(day):
            ts, var_type, var_name, data = event
            value = data.get(DataKeys.VALUE, '')
            units = data.get(DataKeys.UNIT, '')

            _events.append((ts.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                            var_type, var_name, value, units))

        self.write({'events': _events})


class GetEventsHandler(BaseHandler):
    """ Retrieves the list of events matching the given criteria.

    HTTP request arguments:
        start : mandatory start date (format : ISO datetime)
        end : mandatory end date (format : ISO datetime)
        vartype : (optional) type of accepted variables
        varname : (optional) name of requested variable

    Note: either vartype or varname can be provided. If both are given, vartype
    will be ignored.
    """
    def get(self):
        from_time = dateutil.parser.parse(self.get_argument('start'))
        to_time = dateutil.parser.parse(self.get_argument('end'))
        var_name = self.get_argument('varname', None)
        var_type = None if var_name else self.get_argument('vartype', None)

        _events = []
        for event in self._dao.get_events(from_time=from_time, to_time=to_time, var_type=var_type, var_name=var_name):
            ts, var_type, var_name, data = event
            value = data.get(DataKeys.VALUE, '')
            units = data.get(DataKeys.UNIT, '')

            _events.append((ts.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], var_type, var_name, value, units))

        self.write({'events': _events})


class ExportEventsHandler(BaseHandler):
    """ Exports the list of events available for a given day

    HTTP request arguments:
        d : the day (format : "YYYY-MM-DD" or "YYYY/MM/DD")
        f : export format (currently supported: CSV)
    """
    def __init__(self, *args, **kwargs):
        super(ExportEventsHandler, self).__init__(*args, **kwargs)

        self._export_handlers = {
            'csv': self._export_as_csv
        }

    def _export_as_csv(self, events, day):
        self.set_header("Content-Type", "text/csv; charset=UTF-8")
        self.set_header("Content-Disposition", "filename=%s.csv" % day)
        self.write('timestamp;var_type;var_name;data\n')
        for event in events:
            ts, var_type, var_name, data = event
            value = data[DataKeys.VALUE] if data and data.has_key(DataKeys.VALUE) else ''
            units = data[DataKeys.UNIT] if data and data.has_key(DataKeys.UNIT) else ''
            self.write(';'.join((ts.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], var_type, var_name, value, units)) + '\n')

    def get(self):
        day = self.get_argument("d").replace('/', '-')
        fmt = self.get_argument("f", default='csv').lower()
        if fmt not in self._export_handlers:
            raise ValueError("unsupported export format (%s)" % fmt)

        self._export_handlers[fmt](self._dao.get_events_for_day(day), day)


_handlers_initparms = {}

handlers = [
    (r"/days", GetAvailableDaysHandler, _handlers_initparms),
    (r"/dayevents", GetDayEventsHandler, _handlers_initparms),
    (r"/events", GetEventsHandler, _handlers_initparms),
    (r"/export", ExportEventsHandler, _handlers_initparms),
]
