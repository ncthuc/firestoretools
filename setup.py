from setuptools import setup, find_packages

with open('README.md') as readme_file:
    README = readme_file.read()

with open('HISTORY.md') as history_file:
    HISTORY = history_file.read()

setup_args = dict(
    name='firestoretools',
    version='0.1.1',
    description='Useful tools to work with Google Firestore in Python',
    long_description_content_type="text/markdown",
    long_description=README + '\n\n' + HISTORY,
    license='MIT',
    packages=find_packages(exclude=('tests', )),
    author='Thuc Nguyen',
    author_email='gthuc.nguyen@gmail.com',
    keywords=['Firestore', 'Firebase', 'Google Cloud', 'Python 3'],
    url='https://github.com/ncthuc/firestoretools',
    download_url='https://pypi.org/project/firestoretools/',
    # py_modules=['firestoretools'],
    entry_points='''
        [console_scripts]
        firestoretools=firestoretools.firestore_tools:cli
    ''',
)

install_requires = [
    'click',
    'firebase-admin'
]

if __name__ == '__main__':
    setup(**setup_args, install_requires=install_requires)
