.PHONY: clean
clean:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete
	rm -rf dist

.PHONY: deps-clean
deps-clean:
	if command -v pyenv >/dev/null 2>&1; then pyenv local 3.12; fi
	# Remove the environment and ignore errors if it does not exist.
	poetry env remove 3.12 2>/dev/null || true
	poetry env use 3.12

.PHONY: deps
deps: deps-clean
	poetry install

# Clears out all of the tables in the database
.PHONY: db-clean
db-clean:
	psql -U postgres -d postgres -c "DROP SCHEMA IF EXISTS public CASCADE;"
	psql -U postgres -d postgres -c "CREATE SCHEMA public;"

# For ubuntu we get the following error for python 3.9
# `ModuleNotFoundError: No module named 'distutils.cmd'`
# To fix this we must add deadsnakes to the apt registry and install their python 3.9
# packages to fix the problem. This can be removed once we move away from python3.9
.PHONY: install-ubuntu
install-ubuntu: clean deps-clean
	sudo add-apt-repository -y ppa:deadsnakes/ppa
	sudo apt update
	sudo apt install -y python3.9-venv python3.9-dev
	poetry install

# Run the following to clean out the database and run the migrations from scratch to
# prove that they run properly.
.PHONY: migrate
migrate:
	DJANGO_SETTINGS_MODULE=example.settings poetry run django-admin migrate
	poetry run ./manage.py showmigrations --plan

.PHONY: db-setup
db-setup: db-clean migrate

.PHONY: dbrun
dbrun:
	docker compose up

TOX_ARGS ?=
.PHONY: tox
tox:
	poetry run tox $(pytest_args) ${TOX_ARGS}

.PHONY: tests
tests:
	poetry run pytest $(pytest_args)

.PHONY: rollback_migrations
rollback_migrations:
	poetry run ./manage.py migrate oauth2_provider zero
	poetry run ./manage.py migrate drf_integrations zero
	poetry run ./manage.py migrate drf_integrations_example zero

.PHONY: release-test
release-test:
	poetry run twine upload --repository-url https://test.pypi.org/legacy/ dist/*

.PHONY: release
release: static_analysis coverage
	poetry run twine upload dist/*

.PHONY: bump-major
bump-major:
	poetry run bump2version major

.PHONY: bump-minor
bump-minor:
	poetry run bump2version minor

.PHONY: bump-patch
bump-patch:
	poetry run bump2version patch

.PHONY: install-poetry
install-poetry:
	curl -sSL https://install.python-poetry.org | python3 -

.PHONY: uninstall-poetry
uninstall-poetry:
	curl -sSL https://install.python-poetry.org | python3 - --uninstall

.PHONY: coverage
coverage:
	poetry run py.test --cov=drf_integrations tests/ --cov-report html
	@echo Access the report here:
	@echo file://${PWD}/htmlcov/index.html

.PHONY: bundle
bundle: coverage
	rm -r ./dist/ || true
	poetry build
