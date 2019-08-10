from setuptools import setup, find_packages

TESTS_REQUIRES = []
INSTALL_REQUIRES = [
    'aiohttp',
    'aiojobs',
    'marshmallow',
]
setup(
    name='service',
    version='0.0.1',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=INSTALL_REQUIRES,
    tests_requires=TESTS_REQUIRES,
    entry_points={
        'console_scripts': [
            'run-app=service.webservice:main',
        ],
    }
)
