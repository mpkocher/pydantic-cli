.PHONY: package deploy

test:
	nosetests .

package:
	python setup.py sdist bdist_wheel


deploy:
	twine upload dist/*
