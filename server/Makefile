.PHONY: install
install:
	pip install wheel
	pip install -r requirements_dev.txt

.PHONY: sync
sync:
	pip-sync requirements_dev.txt

.PHONY: requirements
requirements: requirements.in requirements_dev.in
	pip-compile -v --generate-hashes --allow-unsafe --output-file requirements.txt requirements.in
	pip-compile -v --generate-hashes --allow-unsafe --output-file requirements_dev.txt requirements_dev.in

.PHONY: upgrade
upgrade:
	pur --patch=Django -r requirements_dev.in
	make requirements

.PHONY: test
test:
	pytest --reuse-db --nomigrations -vs .

.PHONY: test
retest:
	pytest --reuse-db --nomigrations -vvs --lf .
