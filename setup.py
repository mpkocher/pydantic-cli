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
      description='The funniest joke in the world',
      long_description=_read('README.md'),
      url='http://github.com/mpkocher/pydantic-cli',
      author='M. Kocher',
      author_email='michael.kocher@me.com',
      license='MIT',
      packages=['pydantic_cli'],
      tests_require = ['nose'],
      zip_safe=False)
