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


from Plugins.Plugin import PluginDescriptor
from .SkinUtils import loadPluginSkin
from .Debug import logger
from .Version import VERSION
from .JobCockpit import JobCockpit
from .PluginUtils import WHERE_JOBCOCKPIT
from . import _
from .JobSupervisor import JobSupervisor


def main(session, plugin_id="", **__kwargs):
    logger.info("plugin_id: %s", plugin_id)
    session.open(JobCockpit, plugin_id)


def autoStart(reason, **kwargs):
    if reason == 0:  # startup
        if "session" in kwargs:
            logger.info("+++ Version: %s starts...", VERSION)
            loadPluginSkin("skin.xml")
            JobSupervisor.getInstance()
    elif reason == 1:  # shutdown
        logger.info("--- shutdown")


def Plugins(**__kwargs):
    return [
        PluginDescriptor(
            where=[
                PluginDescriptor.WHERE_AUTOSTART,
                PluginDescriptor.WHERE_SESSIONSTART
            ],
            fnc=autoStart
        ),
        PluginDescriptor(
            name="JobCockpit",
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon="JobCockpit.png",
            description=_("Manage Jobs"),
            fnc=main
        ),
        PluginDescriptor(
            name=_("Jobs"),
            description=_("Manage Jobs"),
            where=WHERE_JOBCOCKPIT,
            fnc=main
        )
    ]
