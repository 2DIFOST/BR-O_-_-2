PYTHON ?= python3
export PYTHONPATH := src

.PHONY: run test demo

run:
	$(PYTHON) -m depgraph $(ARGS)

test:
	$(PYTHON) -m unittest discover -s tests -v

demo:
	sh scripts/demo_all.sh
