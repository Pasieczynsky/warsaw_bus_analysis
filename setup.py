import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()
    
setuptools.setup(
    name="WawBus",
    version="0.0.1",
    author="Dominik Pasieczynski",
    author_email="dp448427@students.mimuw.edu.pl",
    description="A package to analyse the data from the buses in Warsaw.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Pasieczynsky/warsaw_bus_analysis",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
