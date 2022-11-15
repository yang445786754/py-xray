import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="python-xray", 
    version="0.3.0",
    author="Tony_9410",
    author_email="tony_9410@foxmail.com",
    description="Python-xray converts Xray commands into python3 methods making it very easy to use xray in any of your python pentesting projects",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yang445786754/py-xray",
    project_urls={
        'Documentation': 'https://github.com/yang445786754/py-xray',
        'How it is used': 'https://github.com/yang445786754/py-xray',
        'Homepage': 'https://github.com/yang445786754/py-xray',
        'Source': 'https://github.com/yang445786754/py-xray'
    },
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    setup_requires=['wheel'],
)
