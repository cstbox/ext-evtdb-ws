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

	@echo "------ removing package marker files required by the IDE"
	$(call rm_devel_file,webservices/__init__.py)
	$(call rm_devel_file,webservices/services/__init__.py)

