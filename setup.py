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

version = '1.3.0'

setup(
    name='nti.contentfragments',
    version=version,
    author='Jason Madden',
    author_email='jason@nextthought.com',
    description="NTI ContentFragments",
    url="https://github.com/NextThought/nti.contentfragments",
    long_description=_read('README.rst') + '\n\n' + _read('CHANGES.rst'),
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
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
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
        # XXX: We deliberately leave this one unspecified. See
        # https://github.com/NextThought/nti.contentfragments/issues/17
        'html5lib',
        # we required lxml implementation details, can't use
        # xml.etree.ElementTree, even on PyPy.
        'lxml >= 4.2.5',
        'repoze.lru >= 0.6',
        'zope.component >= 4.6.1',
        'zope.event >= 4.4.0',
        'zope.interface >= 5.0.0',
        'zope.mimetype >= 2.4.0',
        'zope.security >= 5.1.1',
        'zope.cachedescriptors >= 4.3.1',
        'nti.schema >= 1.14.0',
        # html5lib > 0.99999999 install datrie if appropriate for the platform
        # with its own [datrie] extra. But we do not explicitly depend
        # on that version to help avoid conflicts, and older versions of
        # zc.buildout cannot deal gracefully with missing extras like
        # pip does. See https://github.com/buildout/buildout/issues/457

        # datrie 0.7.1 does not build on CPython 3.7. See
        # https://github.com/pytries/datrie/issues/52

        "datrie >= 0.8.2 ; platform_python_implementation == 'CPython'",
    ],
    extras_require={
        'test': TESTS_REQUIRE,
        'docs': [
            'repoze.sphinx.autointerface',
            'sphinx_rtd_theme',
        ],

    },
    entry_points=entry_points,
)
