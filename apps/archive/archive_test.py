# -*- coding: utf-8; -*-
#
# This file is part of Superdesk.
#
# Copyright 2013, 2014 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license


from superdesk.tests import TestCase
from eve.utils import date_to_str
from . import init_app
from superdesk.utc import get_expiry_date, utcnow
from .archive import ArchiveRemoveExpiredContent


class ArchiveRemoveExpiredContentTestCase(TestCase):

    def setUp(self):
        super().setUp()
        with self.app.app_context():
            self.app.data.insert('archive', [{'expiry': get_expiry_date(-10)}])
            self.app.data.insert('archive', [{'expiry': get_expiry_date(0)}])
            self.app.data.insert('archive', [{'expiry': get_expiry_date(10)}])
            self.app.data.insert('archive', [{'expiry': get_expiry_date(20)}])
            self.app.data.insert('archive', [{'expiry': get_expiry_date(30)}])
            self.app.data.insert('archive', [{'expiry': None}])
            self.app.data.insert('archive', [{'unique_id': 97}])
            init_app(self.app)

    def test_query_getting_expired_content(self):
        with self.app.app_context():
            now = date_to_str(utcnow())
            expiredItems = ArchiveRemoveExpiredContent().get_expired_items(now)
            self.assertEquals(2, expiredItems.count())
