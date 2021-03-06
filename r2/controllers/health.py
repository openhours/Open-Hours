# The contents of this file are subject to the Common Public Attribution
# License Version 1.0. (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://code.reddit.com/LICENSE. The License is based on the Mozilla Public
# License Version 1.1, but Sections 14 and 15 have been added to cover use of
# software over a computer network and provide for limited attribution for the
# Original Developer. In addition, Exhibit A has been modified to be consistent
# with Exhibit B.
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License for
# the specific language governing rights and limitations under the License.
#
# The Original Code is reddit.
#
# The Original Developer is the Initial Developer.  The Initial Developer of
# the Original Code is reddit Inc.
#
# All portions of the code written by reddit are Copyright (c) 2006-2012 reddit
# Inc. All Rights Reserved.
###############################################################################

from threading import Thread
import os
import time
import json

from pylons.controllers.util import abort
from pylons import c, g, response

from reddit_base import MinimalController
from r2.lib.amqp import worker

from validator import *

class HealthController(MinimalController):
    def post(self):
        pass

    def try_pagecache(self):
        pass

    def pre(self):
        pass

    def GET_health(self):
        c.dontcache = True
        response.headers['Content-Type'] = 'text/plain'
        return json.dumps(g.versions, sort_keys=True, indent=4)
