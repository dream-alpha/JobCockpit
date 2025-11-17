# coding=utf-8
#
# Copyright (C) 2018-2025 by dream-alpha
#
# In case of reuse of this source code please do not remove this copyright.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# For more information on the GNU General Public License see:
# <http://www.gnu.org/licenses/>.


from Components.PluginComponent import plugins


WHERE_SEARCH = -99
WHERE_TMDB_SEARCH = -98
WHERE_TMDB_MOVIELIST = -97
WHERE_MEDIATHEK_SEARCH = -96
WHERE_TVMAGAZINE_SEARCH = -95
WHERE_COVER_DOWNLOAD = -94
WHERE_JOBCOCKPIT = -93


def getPlugin(where):
    plugin = None
    plugins_list = plugins.getPlugins(where=where)
    if plugins_list:
        plugin = plugins_list[0]
    return plugin
