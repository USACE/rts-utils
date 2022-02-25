
# PROJECT_NAME defaults to name of the current directory.
PROJECT_NAME = $(notdir $(PWD))
export PROJECT_NAME

THIS_FILE := $(lastword $(MAKEFILE_LIST))

# command arguments passed to test
CMD_ARGS ?= $(cmd)

# all our targets are phony (no files to check).
.PHONY: help

# suppress makes own output
#.SILENT:

# Help
help:
	@echo ""
	@echo "Usage: make [TARGET]"
	@echo "Targets:"
	@echo ""
	@echo ""
	@echo "Extra arguments:"
	@echo ""
	@echo ""

