from setuptools import setup, find_packages

setup(
    name='prodmon',
    version='0.1',
    url='',
    license='',
    author='Chris Strutton',
    author_email='chris@rodandfly.ca',
    description='A collection of python scripts to collect production data from industrial PLC\'s into a mysql database',
    packages=find_packages(include=['prodmon', 'prodmon.*']),
    install_requires=[
        'pylogix~=0.7.0',
        'PyYAML~=5.3.1',
        'Flask~=1.1.2',
        'mysql-connector-python~=8.0.21'
    ]
)
