# ForensicInsertion

This script allows you to insert a local file into a `.dd` disk image (typically a Linux raw disk image) and set its access and modification timestamps.

## Features

- Automatically detects and mounts the largest partition within the image
- Inserts a specified local file into a user-defined path inside the mounted image
- Automatically creates the destination directory inside the image if it does not exist
- Allows setting of custom access time (`atime`) and modification time (`mtime`)
- Unmounts the image after completion, preserving all changes

## Requirements

- Python 3.x
- Root privileges (required for mounting and file operations)
- `partx` (used to parse partition layout)
- `mount`, `umount`, and `touch` utilities

## Usage

```bash
python3 ./insertion/linux.py \
  --image /path/to/image.dd \
  --file /path/to/local/file.png \
  --destination /path/in/linux/image \
  --atime "YYYY-MM-DD HH:MM:SS" \
  --mtime "YYYY-MM-DD HH:MM:SS"
