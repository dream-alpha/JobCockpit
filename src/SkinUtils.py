# coding=utf-8
# Copyright (C) 2018-2025 by dream-alpha
# License: GNU General Public License v3.0 (see LICENSE file for details)


import os
from enigma import getDesktop
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Components.config import config
from .Debug import logger
from .Version import ID, PLUGIN


def getSkinName(skin_name):
    return ID + skin_name


def getScalingFactor():
    return {"HD": 2.0 / 3.0, "FHD": 1, "WQHD": 4.0 / 3.0}[getResolution()]


def getResolution():
    height = getDesktop(0).size().height()
    resolution = "SD"
    if height > 576:
        resolution = "HD"
    if height > 720:
        resolution = "FHD"
    if height > 1080:
        resolution = "WQHD"
    return resolution


def getSkinPath(file_name):
    logger.info(">>> file_name: %s", file_name)
    primary_skin = config.skin.primary_skin.value.split("/")[0]
    logger.debug("primary_skin: %s", primary_skin)

    dirs = [
        os.path.join(resolveFilename(SCOPE_PLUGINS), "Extensions", PLUGIN, "skin", primary_skin),
        os.path.join(resolveFilename(SCOPE_PLUGINS), "SystemPlugins", PLUGIN, "skin", primary_skin),
        os.path.join(resolveFilename(SCOPE_PLUGINS), "Extensions", PLUGIN, "skin"),
        os.path.join(resolveFilename(SCOPE_PLUGINS), "SystemPlugins", PLUGIN, "skin"),
    ]
    logger.debug("dirs: %s", dirs)

    for adir in dirs:
        skin_path = os.path.join(adir, file_name)
        logger.debug("checking: skin_path: %s", skin_path)
        if os.path.exists(skin_path):
            break
        skin_path = ""
    logger.info("skin_path: %s", skin_path)
    return skin_path
