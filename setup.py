from setuptools import setup, find_packages
from setuptools.command.install import install
import subprocess
import sys


class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        install.run(self)
        # Run the config creation hook
        try:
            from crashvault.install_hook import create_user_config
            create_user_config()
        except Exception as e:
            print(f"Warning: Could not create user config: {e}")


setup(
    name="crashvault",
    version="0.2.1",
    description="Lightweight local crash/error vault with CLI",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Creeperkid2014 / AgentArk5",
    license="Custom-Open License",
    url="https://github.com/creeperkid2014/crashvault",
    project_urls={
        "Source": "https://github.com/creeperkid2014/crashvault",
        "Issues": "https://github.com/creeperkid2014/crashvault/issues",
    },
    python_requires=">=3.8",
    packages=find_packages(include=["crashvault", "crashvault.*"]),
    py_modules=[],
    install_requires=["click>=8", "rich"],
    entry_points={"console_scripts": ["crashvault=crashvault.cli:cli"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Environment :: Console",
        "Topic :: System :: Logging",
        "Intended Audience :: Developers",
    ],
    include_package_data=True,
    cmdclass={
        'install': PostInstallCommand,
    },
)
