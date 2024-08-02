run:
	export PYTHONPATH=$(shell pwd); python3 srcs/main.py

BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
ifeq ($(BRANCH),HEAD)
BRANCH := main
endif
pull:
	git fetch --all
	git checkout -f $(BRANCH);
	git reset --hard origin/$(BRANCH);
	git submodule update --init --remote --recursive

push:
	@echo -n "Commit name: "; read name;\
	git add .; git commit -m "$$name"; git push;