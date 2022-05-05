.PHONY: deps
deps:
	poetry env use 3.10
	poetry install

.PHONY: tests
tests: deps
	poetry run pytest --no-migrations
