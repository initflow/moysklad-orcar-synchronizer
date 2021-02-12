from setuptools import setup, find_packages


setup(
    name="moysklad-sync-app",
    version="0.1",
    packages=find_packages(),

    author="Golovnev Dmitry",
    author_email="dmitry.golovnyov@gmail.com",
    description="Moysklad sync app",
    long_description=open("README.md").read(),
    license="BSD",
    url="https://gitlab.com/initflow/django/oscar/moysklad-sync-app",
    include_package_data=True,
    classifiers=[
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Framework :: Django",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],
    install_requires=[
        "Django >= 1.8",
        "django-oscar >= 1.6.2",
        "django-bulk-update >= 2.2.0",
    ],
    zip_safe=True,
)
