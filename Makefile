.PHONY: deps
deps:
	poetry env use 3.9
	poetry install

.PHONY: tests
tests: deps
	poetry run tox $(pytest_args)
	#poetry run pytest --no-migrations
