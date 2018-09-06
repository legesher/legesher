# Copyright 2018 With Madi Co. All Rights Reserved.
#
# Licensed under the MIT License;
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/MIT
#
# Happy Learning!!

# ---------------------------------------------
# General Setup
# ---------------------------------------------

ROOT_DIR := $(realpath .)

# ---------------------------------------------
# Python Version : 2.7
# ---------------------------------------------

ifeq ($(PYTHON),)
	ifneq ($(shell which python2),)
		PYTHON = python2
	else
		PYTHON = python
	endif
endif

PY_DIR := build/lib/python2.7/site-packages
PY_INSTALL_DIR := $(shell $(PYTHON) -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")

export PYTHONPATH := $(ROOT_DIR)/$(PY_DIR)
export PATH := $(ROOT_DIR)/build/bin:$(PATH)
