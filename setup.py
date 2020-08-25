import os
from setuptools import setup


def _get_local_file(file_name):
    return os.path.join(os.path.dirname(__file__), file_name)


def _read(file_name):
    with open(_get_local_file(file_name)) as f:
        return f.read()


def _get_requirements(file_name):
    with open(file_name, 'r') as f:
        reqs = [line for line in f if not line.startswith("#")]
    return reqs


def get_version():
    p = _get_local_file(os.path.join("pydantic_cli", "_version.py"))
    matcher = "__version__"

    with open(p) as f:
        for line in f:
            if matcher in line:
                version = line.split("=")[1].strip().replace('"', '')
                return version

    raise ValueError(f"Unable to find version {matcher} in file={p}")


setup(name='pydantic_cli',
      version=get_version(),
      description='Turn Pydantic defined Data Models into CLI Tools',
      long_description=_read('README.md'),
      long_description_content_type="text/markdown",
      url='http://github.com/mpkocher/pydantic-cli',
      author='M. Kocher',
      author_email='michael.kocher@me.com',
      license='MIT',
      python_requires=">=3.7",
      install_requires=_get_requirements("REQUIREMENTS.txt"),
      packages=['pydantic_cli', 'pydantic_cli.examples'],
      tests_require=_get_requirements("REQUIREMENTS-TEST.txt"),
      extras_require={"shtab": "shtab>=1.3.1"},
      zip_safe=False,
      classifiers=[
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.7",
          "Programming Language :: Python :: 3.8",
          "Programming Language :: Python :: 3.9",
          "License :: OSI Approved :: MIT License",
          "Operating System :: OS Independent",
          "Topic :: Utilities",
          "Topic :: Software Development",
          "Typing :: Typed",
      ]
      )
