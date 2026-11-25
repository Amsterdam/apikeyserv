.PHONY: install
install:
	uv sync

.PHONY: sync
sync:
	uv sync

.PHONY: upgrade
upgrade:
	uv lock --upgrade
	uv sync

.PHONY: test
test:
	uv run pytest --reuse-db --nomigrations -vs .

.PHONY: test
retest:
	uv run pytest --reuse-db --nomigrations -vvs --lf .
