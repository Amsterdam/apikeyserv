.PHONY: install
install:
	pip install wheel
	pip install -r requirements_dev.txt

.PHONY: sync
sync:
	pip-sync requirements_dev.txt

.PHONY: requirements
requirements: requirements.in requirements_dev.in
	pip-compile -v --generate-hashes --output-file requirements.txt requirements.in
	pip-compile -v --generate-hashes --output-file requirements_dev.txt requirements_dev.in

.PHONY: upgrade
upgrade:
	pur --patch=Django -r requirements_dev.in
	pip-compile -v --generate-hashes --upgrade --output-file requirements.txt requirements.in
	pip-compile -v --generate-hashes --upgrade --output-file requirements_dev.txt requirements_dev.in

.PHONY: test
test:
	pytest --reuse-db --nomigrations -vs .

.PHONY: test
retest:
	pytest --reuse-db --nomigrations -vvs --lf .
