.PHONY: check self-test check-all

check:
	python3 tools/docs_check.py

self-test:
	python3 tools/docs_check.py --self-test

check-all: self-test check
