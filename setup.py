
from setuptools import setup
import asyncmrws

setup(
    name='asyncmrws',
    version=asyncmrws.__version__,
    description='MrWorkServer client for Python Asyncio',
    long_description='Asyncio based Python client for MrWorkServer',
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8'
        ],
    url='https://github.com/MarkReedZ/asyncmrws',
    author='Mark Reed',
    author_email='mark@untilfluent.com',
    license='MIT License',
    packages=['asyncmrws'],
    zip_safe=True,
)

