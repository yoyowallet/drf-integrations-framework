.PHONY: deps
deps:
	if command -v pyenv >/dev/null 2>&1; then pyenv local 3.12; fi
	poetry env remove 3.12 || true
	poetry env use 3.12
	poetry install

# Clears out all of the tables in the database
.PHONY: db-clean
db-clean:
	psql -U postgres -d postgres -c "DROP SCHEMA IF EXISTS public CASCADE;"
	psql -U postgres -d postgres -c "CREATE SCHEMA public;"

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

.PHONY: tox
tox:
	poetry run tox $(pytest_args)

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
