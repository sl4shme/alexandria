from setuptools import setup

setup(
    name='alexandria',
    version='0.0.1',
    description='Alexandria is an “inventory as a service” application',
    url='https://github.com/uggla/alexandria',
    author='Alexandria Team',
    author_email='alexandria-devel@mondorescue.org',
    license='Apache Software License',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
    ],

    keywords='inventory cmdb openstack',

    packages=["alexandria"],

    scripts=["alexandria/app.py"]
)
