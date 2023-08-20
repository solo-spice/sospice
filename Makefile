.PHONY: build install install-editable, test, test-htmlcov, pre-commit, show-version, doc-html, publish

build:
	python3 -m build
install:
	python -m pip install .
install-editable:
	python -m pip install -e .
test: show-version
	pytest --cov
test-htmlcov: show-version
	pytest --cov --cov-report html
pre-commit:
	pre-commit
show-version:
	python -m setuptools_scm
doc-html:
	make -C docs html
publish:
	@echo "Please make sure that:"
	@echo "* changes have been merged to the main branch, with correct git tag in Github and version information in sospice/_version.py"
	@echo "* a build has been done for this version"
	@echo "Please press <Enter> to confirm"
	@read foo
	python3 -m twine upload --verbose dist/*
