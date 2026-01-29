from setuptools import setup, find_packages


setup(
    name="pyStateView",
    version="1.0.0",
    description="Industrial discrete state timeline visualization widgets for PyQt5",
    packages=find_packages(),
    install_requires=["PyQt5>=5.15"],
    include_package_data=True,
)
