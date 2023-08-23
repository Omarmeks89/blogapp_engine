import os
from setuptools import setup, find_packages


if __name__ == "__main__":
    setup(
        name="async_blog_engine",
        version=os.getenv("PACKAGE_VERSION", "0.1.dev0"),
        package_dir={"": "app"},
        packages=find_packages(where="src"),
        description="test assembly",
    )
