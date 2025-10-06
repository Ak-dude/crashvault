from setuptools import setup

setup(
    name="crashvault",
    version="0.2.0",
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
    py_modules=["crashvault"],
    install_requires=["click>=8"],
    entry_points={"console_scripts": ["crashvault=crashvault:cli"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Environment :: Console",
        "Topic :: System :: Logging",
        "Intended Audience :: Developers",
    ],
    include_package_data=True,
)
