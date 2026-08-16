from pathlib import Path

# Directories to ignore
IGNORE_DIRS = {
    ".git",
    ".idea",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "node_modules",
    "dist",
    "build",
}

# File extensions to ignore (optional)
IGNORE_EXTENSIONS = {
    ".pyc",
    ".pyo",
}

def print_tree(directory: Path, prefix: str = ""):
    entries = sorted(
        [
            e for e in directory.iterdir()
            if e.name not in IGNORE_DIRS
            and e.suffix not in IGNORE_EXTENSIONS
        ],
        key=lambda x: (x.is_file(), x.name.lower())
    )

    for i, entry in enumerate(entries):
        connector = "└── " if i == len(entries) - 1 else "├── "
        print(prefix + connector + entry.name)

        if entry.is_dir():
            extension = "    " if i == len(entries) - 1 else "│   "
            print_tree(entry, prefix + extension)

if __name__ == "__main__":
    root = Path.cwd()  # Current project directory
    print(root.name)
    print_tree(root)