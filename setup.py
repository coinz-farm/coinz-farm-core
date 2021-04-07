import setuptools


with open("README.md") as fp:
    long_description = fp.read()

CDK_VER = '1.97.0'

setuptools.setup(
    name="cdk",
    version="0.0.1",

    description="An empty CDK Python app",
    long_description=long_description,
    long_description_content_type="text/markdown",

    author="author",

    package_dir={"": "cdk"},
    packages=setuptools.find_packages(where="cdk"),

    install_requires=[
        f"aws-cdk.aws-certificatemanager=={CDK_VER}",
        f"aws-cdk.core=={CDK_VER}",
        f"aws-cdk.aws-ecs=={CDK_VER}",
        f"aws-cdk.aws-elasticloadbalancingv2=={CDK_VER}",
        f"aws-cdk.aws-route53=={CDK_VER}",
        f"aws-cdk.aws-s3=={CDK_VER}"
    ],

    python_requires=">=3.8",

    classifiers=[
        "Development Status :: 4 - Beta",

        "Intended Audience :: Developers",

        "License :: OSI Approved :: Apache Software License",

        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",

        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",

        "Typing :: Typed",
    ],
)
