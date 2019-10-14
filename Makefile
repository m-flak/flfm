SUBDIRS = flfm

.PHONY: all

all:
	@set -e; for dir in $(SUBDIRS); do \
	make -C $$dir; \
	done

docs:
	@set -e; cd ./doc; cp ../README.md ./README.md; \
	cp ../systemd/flfm.service ./flfm.service; \
	cp ../nginx/example_nginx.conf ./example_nginx.conf; \
	make html
