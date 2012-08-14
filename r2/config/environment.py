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

import os
import mimetypes

from pylons import config

import r2.config
import r2.lib.helpers
from r2.config import routing
from r2.lib.app_globals import Globals
from r2.lib.configparse import ConfigValue
from r2.lib.plugin import PluginLoader
from r2.templates import tmpl_dirs


mimetypes.init()


def load_environment(global_conf={}, app_conf={}, setup_globals=True):
    # Setup our paths
    root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    paths = {'root': root_path,
             'controllers': os.path.join(root_path, 'controllers'),
             'templates': tmpl_dirs,
             }

    if ConfigValue.bool(global_conf.get('uncompressedJS')):
        paths['static_files'] = os.path.join(root_path, 'public')
    else:
        paths['static_files'] = os.path.join(os.path.dirname(root_path), 'build/public')

    config.init_app(global_conf, app_conf, package='r2',
                    template_engine='mako', paths=paths)

    g = config['pylons.g'] = Globals(global_conf, app_conf, paths)
    if setup_globals:
        g.setup()
        r2.config.cache = g.cache

    config['pylons.h'] = r2.lib.helpers

    g.plugins = config['r2.plugins'] = PluginLoader().load_plugins(g.config.get('plugins', []))
    config['routes.map'] = routing.make_map()

    #override the default response options
    config['pylons.response_options']['headers'] = {}

    # The following template options are passed to your template engines
    #tmpl_options = {}
    #tmpl_options['myghty.log_errors'] = True
    #tmpl_options['myghty.escapes'] = dict(l=webhelpers.auto_link, s=webhelpers.simple_format)

    tmpl_options = config['buffet.template_options']
    tmpl_options['mako.filesystem_checks'] = getattr(g, 'reload_templates', False)
    tmpl_options['mako.default_filters'] = ["mako_websafe"]
    tmpl_options['mako.imports'] = \
                                 ["from r2.lib.filters import websafe, unsafe, mako_websafe",
                                  "from pylons import c, g, request",
                                  "from pylons.i18n import _, ungettext"]
    
    # Add your own template options config options here,
    # note that all config options will override
    # any Pylons config options

    # Return our loaded config object
    #return config.Config(tmpl_options, map, paths)
