from setuptools import setup, find_packages

setup(
    name='fipl_config',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'pydantic==2.5.3',
        'ast-comments==1.2.1',
        'pandas==2.2.1',
        'selenium==4.18.1',
        'beautifulsoup4==4.12.0',
        'requests==2.31.0',
        'ghapi==1.0.4'
    ],
)