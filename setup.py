"""Setuptools for HFormat"""

from setuptools import setup
import pathlib

here = pathlib.Path(__file__).parent.resolve()
long_descr = (here / "README.md").read_text(encoding="utf-8")
setup(
      name = "hformat",
      version = "0.1.0a1",
      description = "A custom human-intelligible str.format()",
      long_description = long_descr,
      long_description_content_type = "text/markdown",
      url = "https://github.com/angmorpri/hformat",
      author = "Ángel Moreno",
      author_email = "angelmorenoprieto@gmail.com",
      # license = "MIT",
      classifiers = [
      	'Development Status :: 3 - Alpha',
      	'License :: OSI Approved :: MIT License',
      	'Programming Language :: Python :: 2',
      	'Programming Language :: Python :: 3',
      	'Topic :: Software Development :: Libraries',
      ],
      keywords = "format, string",
      python_requires = ">=2.7, <4",
      package_data = {
      	'hformat': ['functions.yml'],
      },
)
