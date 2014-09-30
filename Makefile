# CSTBox framework
#
# Makefile for building the Debian distribution package containing the
# event database Web services API extension module.
#
# author = Eric PASCUAL - CSTB (eric.pascual@cstb.fr)

# name of the CSTBox module
MODULE_NAME=ext-evtdb-ws

include $(CSTBOX_DEVEL_HOME)/lib/makefile-dist.mk

copy_files: \
	copy_python_files

