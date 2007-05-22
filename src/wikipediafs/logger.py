# -*- coding: utf-8 -*-

# WikipediaFS
# Copyright (C) 2005 - 2007 Mathieu Blondel
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import logging
import os, os.path
from config import CONFIG

conf_dir = os.path.join(os.environ['HOME'], '.wikipediafs')
file = os.path.join(conf_dir, 'wikipediafs.log')

# Creates .wikipediafs. in HOME if needed
if not os.path.exists(conf_dir):
    os.mkdir(conf_dir,0700)

LOGGER = logging.getLogger('wikipediafs')
hdlr = logging.FileHandler(file)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
LOGGER.addHandler(hdlr)

if CONFIG.debug_mode:
    LOGGER.setLevel(logging.DEBUG)
else:
    LOGGER.setLevel(logging.INFO)

# LOGGER.debug('A debug message')
# LOGGER.info('Some information')
# LOGGER.warning('A shot across the bows')
# LOGGER.error('error...')
