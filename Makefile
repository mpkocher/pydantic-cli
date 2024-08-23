.PHONY: package deploy mypy

test:
	pytest

pkg:
	hatch build


deploy:
	twine upload dist/*

mypy:
	mypy pydantic_cli

format:
	black pydantic_cli

clean:
	rm -rf build dist *.egg-info
