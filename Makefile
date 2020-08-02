.PHONY: package deploy mypy

test:
	pytest

package:
	python setup.py sdist bdist_wheel


deploy:
	twine upload dist/*

mypy:
	mypy pydantic_cli

format:
	black pydantic_cli

clean:
	rm -rf build dist *.egg-info
