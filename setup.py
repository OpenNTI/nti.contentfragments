import codecs
from setuptools import setup, find_packages

VERSION = '0.0.0'

entry_points = {
    'console_scripts': [
    ],
}

TESTS_REQUIRE = [
    'nose2[coverage_plugin]',
    'pyhamcrest',
    'zope.testing',
    'nti.testing'
]

import platform
py_impl = getattr(platform, 'python_implementation', lambda: None)
IS_PYPY = py_impl() == 'PyPy'

setup(
    name='nti.contentfragments',
    version=VERSION,
    author='Jason Madden',
    author_email='jason@nextthought.com',
    description="NTI ContentFragments",
    long_description=codecs.open('README.rst', encoding='utf-8').read(),
    license='Proprietary',
    keywords='Content fragments',
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython'
    ],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['nti'],
    tests_require=TESTS_REQUIRE,
    install_requires=[
        'setuptools',
        'dolmen.builtins',
        'html5lib[datrie]', # > 0.99999999 install datrie if appropriate for the platform
        'lxml', # we required lxml implementation details, can't use xml.etree.ElementTree, even on PyPy.
        'plone.i18n < 3.0', # 3.0 adds hards deps on Products.CMFCore and Zope2
        'repoze.lru',
        'zope.browserresource',
        'zope.component',
        'zope.event',
        'zope.interface',
        'zope.mimetype',
        'zope.security',
        'zope.vocabularyregistry',
        'zope.cachedescriptors',
        'nti.schema'
    ],
    extras_require={
        'test': TESTS_REQUIRE,
    },
    dependency_links=[
        'git+https://github.com/NextThought/nti.schema.git#egg=nti.schema',
        'git+https://github.com/NextThought/nti.testing.git#egg=nti.testing',
    ],
    entry_points=entry_points
)
