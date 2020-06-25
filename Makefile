.PHONY: package deploy mypy

test:
	nosetests .

package:
	python setup.py sdist bdist_wheel


deploy:
	twine upload dist/*

mypy:
	mypy pydantic_cli
