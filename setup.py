from setuptools import setup

setup(
    author="CS50",
    author_email="sysadmins@cs50.harvard.edu",
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
    description="CS50 library for Python",
    install_requires=["Flask>=1.0", "SQLAlchemy", "sqlparse", "termcolor"],
    keywords="cs50",
    name="cs50",
    package_dir={"": "src"},
    packages=["cs50"],
    url="https://github.com/cs50/python-cs50",
    version="5.0.0"
)
