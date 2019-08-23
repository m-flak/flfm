SUBDIRS = flfm

.PHONY: all

all:
	@set -e; for dir in $(SUBDIRS); do \
	make -C $$dir; \
	done
