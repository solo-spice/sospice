install:
	python -m pip install .
test:
	pytest --cov
test-html:
	pytest --cov --cov-report html
pre-commit:
	pre-commit