# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011, 2012 MediaGoblin contributors.  See AUTHORS.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import shutil

from mediagoblin import mg_globals
from mediagoblin.tests.tools import (
    TEST_USER_DEV, suicide_if_bad_celery_environ)


def setup_package():
    suicide_if_bad_celery_environ()

    import warnings
    from sqlalchemy.exc import SAWarning
    warnings.simplefilter("error", SAWarning)


def teardown_package():
    # Remove and reinstall user_dev directories
    if os.path.exists(TEST_USER_DEV):
        shutil.rmtree(TEST_USER_DEV)
