from setuptools import setup, find_packages
import sys, os

version = '0.5.0'

setup(name='astkit',
      version=version,
      description="A collection of tools and utilities built on the ast (python >=  2.6) module.",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='ast',
      author='Matthew J Desmarais',
      author_email='matthew.desmarais@gmail.com',
      url='https://bitbucket.org/desmaj/astkit',
      license='GPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
