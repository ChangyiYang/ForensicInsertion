import subprocess
import os
import getpass
import shutil
import re
import argparse
import time
from datetime import datetime


def run_sudo_command(command):
    sudo_command = f"echo {password} | sudo -S {command}"
    process = subprocess.Popen(sudo_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        print(f"Error: {stderr.decode()}")
        return None
    else:
        return stdout.decode()


def get_largest_partition_offset(image_file):
    result = run_sudo_command(f"partx -b {image_file}")
    if not result:
        print("Error: Could not retrieve partition layout.")
        return None

    partitions = []
    for line in result.splitlines():
        partition_regex = r'(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([a-f0-9\-]+)'
        match = re.search(partition_regex, line)
        if match:
            start = int(match.group(2))
            sectors = int(match.group(4))
            partitions.append((start, sectors))

    if not partitions:
        print("No partitions found.")
        return None

    largest_partition = max(partitions, key=lambda x: x[1])
    return largest_partition[0] * 512


def mount_image(image_file, mount_point):
    partition_offset = get_largest_partition_offset(image_file)
    if partition_offset is None:
        print("Error: Could not detect partition offset.")
        return

    run_sudo_command(f"mkdir -p {mount_point}")
    mount_command = f"mount -o loop,offset={partition_offset} {image_file} {mount_point}"
    run_sudo_command(mount_command)


def unmount_image(mount_point):
    run_sudo_command(f"umount {mount_point}")


def set_file_timestamp(filepath, access_time, modified_time):
    try:
        atime_fmt = datetime.strptime(access_time, "%Y-%m-%d %H:%M:%S").strftime("%Y%m%d%H%M.%S")
        mtime_fmt = datetime.strptime(modified_time, "%Y-%m-%d %H:%M:%S").strftime("%Y%m%d%H%M.%S")

        run_sudo_command(f"touch -a -t {atime_fmt} '{filepath}'")
        run_sudo_command(f"touch -m -t {mtime_fmt} '{filepath}'")

        print(f"Timestamps updated: atime={access_time}, mtime={modified_time}")
    except Exception as e:
        print(f"Failed to update timestamp: {e}")




def insert_file_into_image(local_file, destination_path, access_time, modified_time):
    if not os.path.exists(local_file):
        print(f"Error: {local_file} does not exist.")
        return
    # Ensure destination directory exists
    run_sudo_command(f"mkdir -p '{os.path.dirname(destination_path)}'")

    run_sudo_command(f"cp {local_file} {destination_path}")
    set_file_timestamp(destination_path, access_time, modified_time)
    print(f"File {local_file} copied to {destination_path} and timestamps updated.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Insert a file into a mounted disk image.")
    parser.add_argument("--image", required=True, help="Path to the .dd image file.")
    parser.add_argument("--file", required=True, help="Path to the local file to insert.")
    parser.add_argument("--destination", required=True, help="Target path inside the mounted image (e.g., /mnt/linux_data/subfolder)")
    parser.add_argument("--ctime", help="Desired creation time (ignored, not settable).")
    parser.add_argument("--mtime", required=True, help="Desired modification time (format: 'YYYY-MM-DD HH:MM:SS').")
    parser.add_argument("--atime", required=True, help="Desired access time (format: 'YYYY-MM-DD HH:MM:SS').")

    args = parser.parse_args()

    image_file = args.image
    local_file = args.file
    access_time = args.atime
    modified_time = args.mtime
    mount_point = "/mnt/linux_data"

    print(f"Using mount point: {mount_point}")

    # User wants path like /home/secret inside image
    relative_destination = args.destination.lstrip("/")
    destination_path = os.path.join(mount_point, relative_destination, os.path.basename(local_file))

    print(f"Final file will be placed at: {destination_path}")

    if not os.path.exists(image_file):
        print(f"Error: Disk image not found: {image_file}")
        exit(1)
    if not os.path.exists(local_file):
        print(f"Error: Local file not found: {local_file}")
        exit(1)

    password = getpass.getpass("Enter your sudo password: ")

    print("Mounting disk image...")
    mount_image(image_file, mount_point)

    print("Inserting file and modifying timestamp...")
    insert_file_into_image(local_file, destination_path, access_time, modified_time)

    print("Unmounting image...")
    unmount_image(mount_point)
