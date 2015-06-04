import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'pyramid',
    'SQLAlchemy',
    'transaction',
    'pyramid_tm',
    'pyramid_debugtoolbar',
    'zope.sqlalchemy',
    'waitress',
    'python-dateutil',
    'pyparsing',
    'scipy',
    'numpy',
    'matplotlib',
    'MDP',
    'pandas',
    'iso3166'
    ]

setup(name='msaf',
      version='0.1',
      description='msaf',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='',
      author_email='',
      url='',
      keywords='web wsgi bfg pylons pyramid',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='msaf',
      install_requires=requires,
      entry_points="""\
      [paste.app_factory]
      main = msaf:main
      [console_scripts]
      msaf-setup = msaf.scripts.setup:main
      msaf-csv2dict = msaf.scripts.csv2dict:main
      """,
      )

