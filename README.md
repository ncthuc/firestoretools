Useful tools to work with Google Cloud Firestore database in Python

# Description
    
Main functions

- `read`: recursively read collections and documents, and save to disk. Useful for backup operation.
- `write`: write whole folder with arbitrary levels of nested structure. Useful for restore operation.

# Installation
 
## Normal installation

```bash
pip install firestoretools
```

## Development installation

```bash
git clone https://github.com/ncthuc/firestoretools.git
cd firestoretools
pip install --editable .
```

# Usage
## Backup data
```bash
firestoretools read --help
```

## Restore data
```bash
firestoretools write --help
```