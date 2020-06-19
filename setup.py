import os
from setuptools import setup

version = __import__('pydantic_cli').__version__


def _get_local_file(file_name):
    return os.path.join(os.path.dirname(__file__), file_name)


def _read(file_name):
    with open(_get_local_file(file_name)) as f:
        return f.read()


setup(name='pydantic_cli',
      version=version,
      description='Turn Pydantic defined Data Models into CLI Tools',
      long_description=_read('README.md'),
      long_description_content_type="text/markdown",
      url='http://github.com/mpkocher/pydantic-cli',
      author='M. Kocher',
      author_email='michael.kocher@me.com',
      license='MIT',
      packages=['pydantic_cli', 'pydantic_cli.examples'],
      tests_require = ['nose'],
      zip_safe=False,
      classifiers=[
          "Programming Language :: Python :: 3",
          "License :: OSI Approved :: MIT License",
          "Operating System :: OS Independent",
      ]
      )
