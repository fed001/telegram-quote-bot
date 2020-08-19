from setuptools import setup, find_packages


def readme():
      with open('README.md') as f:
            return f.read()


setup(
      name="telegram_quote_bot",
      version="1.0.0",
      packages=find_packages(),
      include_package_data=True
)
