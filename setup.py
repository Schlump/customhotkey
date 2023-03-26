from setuptools import setup

setup(
    name="customhotkey",
    version="0.1",
    description="",
    url="",
    author="",
    author_email="",
    install_requires=["pyyaml", "evdev"],
    packages=["customkey"],
    scripts=[
        "bin/ck",
    ],
    zip_safe=False,
)
