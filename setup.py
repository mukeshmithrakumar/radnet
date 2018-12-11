import setuptools
from setuptools import find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

REQUIRED_PACKAGES = ['pytorch', 'tifffile', 'pillow', 'opencv', 'scipy']

setuptools.setup(
    name="U-Net",
    version="1.0.0",
    author="Mukesh Mithrakumar",
    author_email="mukesh.mithrakumar@jacks.sdstate.edu",
    description="PyTorch implementation of U-Net for biomedical image segmentation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mukeshmithrakumar/",
    classifiers=(
        "Development Status :: 1.0.0.dev1 - Development release",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    keywords="sample setuptools development",
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    install_requires=REQUIRED_PACKAGES,
    entry_points={
        'console_scripts': [
            'u_net_task = U-Net.trainer.task:main',
            'u_net_train = U-Net.trainer.train:train',
            'u_net_evaluate = U-Net.trainer.evaluate:evaluate',
        ]
    },
    python_requires='>=3',
)
