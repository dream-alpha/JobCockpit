# coding=utf-8
# Copyright (C) 2018-2025 by dream-alpha
# License: GNU General Public License v3.0 (see LICENSE file for details)


from Plugins.Plugin import PluginDescriptor
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
