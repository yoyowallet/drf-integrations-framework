.PHONY: help
help:
	@echo "Please use 'make <target>' where <target> is one of"
	@echo "  deps                 to install dependencies for local development"
	@echo "  clean                to clean up environment"
	@echo "  lint                 runs linting on all the files using Ruff"
	@echo "  tests                to run tests"
	@echo "  coverage             to run code coverage"
	@echo "  install-poetry       installs the correct version poetry"
	@echo "  uninstall-poetry     uninstalls poetry if things go wrong."
	@echo "  tree                 Produces and ASCII directory tree to provide AI bots with context of the project."
	@echo "  showoutdatedpackages Ask poetry for a list of top-level packages that can be updated."

.PHONY: deps
deps:
	poetry env remove 3.9
	poetry env use 3.9
	poetry install

.PHONY: lint
lint:
	poetry run pre-commit run --all-files

.PHONY: clean
clean:
	rm -rf .tox/ .pytest_cache/ dist/ htmlcov/ .coverage coverage.xml db.sqlite3
	find . -type f -name "*.pyc" -delete

.PHONY: tests
tests: coverage
	# ensure that `docker compose up` is running to start the redis server before
	# running these tests.
	poetry run tox $(pytest_args)

.PHONY: coverage
coverage: lint
	poetry run py.test --cov=idempotency_key tests/ --cov-report html
	@echo Access the report here:
	@echo file://${PWD}/htmlcov/index.html

.PHONY: install-poetry
install-poetry:
	curl -sSL https://install.python-poetry.org | python3 -

.PHONY: uninstall-poetry
uninstall-poetry:
	curl -sSL https://install.python-poetry.org | python3 - --uninstall

.PHONY: tree
tree:
	tree -I __pycache__ -I *.pyc 2>/dev/null

.PHONY: showoutdatedpackages
showoutdatedpackages:
	poetry show --outdated -T
