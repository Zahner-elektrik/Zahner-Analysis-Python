import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="zahner_analysis",
    version="1.0.3",
    author="Maximilian Krapp",
    author_email="maximilian.krapp@zahner.de",
    description="Python package for the analysis of electrochemical impedance spectra.",
    keywords=[
        "potentiostat, electrochemistry, chemistry, eis, cyclic voltammetry, fuel-cell, battery"
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://zahner.de/",
    project_urls={
        "Documentation": "https://doc.zahner.de/zahner_analysis",
        "Examples": "https://github.com/Zahner-elektrik/Zahner-Analysis-Python/tree/main/Examples",
        "Source Code": "https://github.com/Zahner-elektrik/Zahner-Analysis-Python",
        "Bug Tracker": "https://github.com/Zahner-elektrik/Zahner-Analysis-Python/issues",
    },
    packages=setuptools.find_packages(where="."),
    license="MIT",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Education",
        "Intended Audience :: Manufacturing",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Chemistry",
        "Topic :: Scientific/Engineering :: Physics",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "numpy",
        "matplotlib",
        "requests",
    ],
    platforms="any",
)
