from setuptools import setup

setup(
    name='prodmon',
    version='0.1',
    packages=['prodmon', 'prodmon.shared', 'prodmon.db_post', 'prodmon.web_config', 'prodmon.plc_collect'],
    url='',
    license='',
    author='Chris Strutton',
    author_email='chris@rodandfly.ca',
    description='A collection of python scripts to collect production data from industrial PLC\'s into a mysql database'
)
