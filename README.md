# ForensicInsertion

**ForensicInsertion** is a project designed to automatically simulate realistic user activities by generating, downloading, selecting, and inserting files into a `.dd` Linux disk image, while preserving plausible file system traces such as access and modification times.

## Overview

This tool reconstructs simulated user behavior inside a Linux environment by:
- Generating realistic search queries based on a user activity description
- Downloading documents, images, audio, and video files according to those queries
- Selecting and planning plausible file system activities
- Inserting selected files into a mounted Linux disk image
- Setting appropriate file access (`atime`) and modification (`mtime`) timestamps
- Unmounting the disk image after modifications

It can be used for forensic an alysis training, system recovery testing, anti-forensics research, and educational purposes.

## Features

- Generate search queries using LLMs (GPT-4o) based on user activity descriptions
- Download documents, images, audios, and videos from public sources
- Select relevant downloaded files and assign realistic file paths and timestamps
- Detect and mount the largest partition in a `.dd` disk image
- Insert files into the mounted filesystem and update their timestamps
- Full automation of the entire process with minimal manual intervention
- Verbose mode for detailed execution logging

## Requirements

- Python 3.8+
- Root privileges (required for mounting disk images and modifying file timestamps)
- Chrome browser and Chromedriver for Selenium
- System utilities:
  - `partx` (for partition table parsing)
  - `mount`, `umount`, and `touch` (for filesystem operations)
  - `ffmpeg` (for audio processing with yt-dlp)
- OpenAI API Key for LLM-based query generation and file selection

### Python Dependencies

Install required Python packages:

```bash
pip install -r requirements.txt
```

Recommended to use `pipreqs` to regenerate `requirements.txt` if changes are made.

### System Packages

Install necessary system tools on Ubuntu:

```bash
sudo apt install util-linux ffmpeg chromium-driver
```

## Project Structure

| Folder/File | Description |
|:---|:---|
| `insertion/` | Disk image mounting, file insertion, and timestamp setting logic |
| `LLM/` | LLM-based search query generation and file selection planning |
| `to_upload/` | Temporary storage for downloaded files (organized into subfolders) |
| `main.py` | Main entry point script orchestrating the full pipeline |

## Usage

1. Prepare a clean Linux `.dd` disk image.
2. Run the main program:

```bash
python main.py
```

3. Follow the prompts:
   - Enter a **user activity description** (e.g., "I was researching polar bears and climate change").
   - Specify the path to your `.dd` disk image when prompted.
4. The tool will automatically:
   - Generate search queries
   - Download relevant files
   - Select plausible files
   - Insert files into the mounted image
   - Set correct timestamps
   - Unmount the image safely

5. You can enable verbose mode for detailed logs:

```bash
python main.py -v
```

## Example

```plaintext
Enter the user activity description: I was reading cat care articles and watching cat videos
Downloading files...
Selecting relevant files...
Mounting disk image...
Inserting files and setting timestamps...
Unmounting disk image...
All operations completed successfully.
```

## Notes

- Requires a valid `.env` file with an `OPENAI_API_KEY` for LLM functionality.
- Files are organized by type under `./to_upload/`.
- Designed to run on Linux systems with administrative (sudo) privileges.

## Disclaimer

This tool is intended for **educational and research purposes only**. Use responsibly and ethically in compliance with local regulations.
