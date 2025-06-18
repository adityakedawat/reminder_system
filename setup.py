from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="reminder-system",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A comprehensive reminder system using MailerSend API and Supabase",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/reminder_system",
    packages=find_packages(where="src/python"),
    package_dir={"": "src/python"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "reminder-system=reminder_system.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
) 