import codecs
from setuptools import setup, find_packages



entry_points = {
    'console_scripts': [
    ],
}

TESTS_REQUIRE = [
    'pyhamcrest',
    'zope.testing',
    'nti.testing',
    'zope.testrunner',
]

def _read(fname):
    with codecs.open(fname, encoding='utf-8') as f:
        return f.read()

version = _read('version.txt').strip()

setup(
    name='nti.contentfragments',
    version=version,
    author='Jason Madden',
    author_email='jason@nextthought.com',
    description="NTI ContentFragments",
    url="https://github.com/NextThought/nti.contentfragments",
    long_description=_read('README.rst'),
    license='Apache',
    keywords='Content fragments semantic typing interfaces classes sanitize censor',
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    namespace_packages=['nti'],
    zip_safe=True, # zope.mimetype uses open() though, so we may have to extract files
    tests_require=TESTS_REQUIRE,
    install_requires=[
        'setuptools',
        'html5lib[datrie]', # > 0.99999999 install datrie if appropriate for the platform
        'lxml', # we required lxml implementation details, can't use xml.etree.ElementTree, even on PyPy.
        'repoze.lru',
        'zope.component',
        'zope.event',
        'zope.interface',
        'zope.mimetype >= 2.1.0',
        'zope.security',
        'zope.cachedescriptors',
        'nti.schema'
    ],
    extras_require={
        'test': TESTS_REQUIRE,
    },
    entry_points=entry_points,
)
