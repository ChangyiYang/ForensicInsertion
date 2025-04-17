import subprocess
import os
import getpass
import re
from datetime import datetime


def run_sudo_command(command, password):
    sudo_command = f"echo {password} | sudo -S {command}"
    process = subprocess.Popen(sudo_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        print(f"Error: {stderr.decode()}")
        return None
    else:
        return stdout.decode()


def get_largest_partition_offset(image_file, password):
    result = run_sudo_command(f"partx -b {image_file}", password)
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


def mount_image(image_file, mount_point, password):
    partition_offset = get_largest_partition_offset(image_file, password)
    if partition_offset is None:
        raise RuntimeError("Could not detect partition offset.")

    run_sudo_command(f"mkdir -p {mount_point}", password)
    mount_command = f"mount -o loop,offset={partition_offset} {image_file} {mount_point}"
    run_sudo_command(mount_command, password)


def unmount_image(mount_point, password):
    run_sudo_command(f"umount {mount_point}", password)


def set_file_timestamp(filepath, access_time, modified_time, password):
    try:
        atime_fmt = datetime.strptime(access_time, "%Y-%m-%d %H:%M:%S").strftime("%Y%m%d%H%M.%S")
        mtime_fmt = datetime.strptime(modified_time, "%Y-%m-%d %H:%M:%S").strftime("%Y%m%d%H%M.%S")

        run_sudo_command(f"touch -a -t {atime_fmt} '{filepath}'", password)
        run_sudo_command(f"touch -m -t {mtime_fmt} '{filepath}'", password)

        print(f"Timestamps updated: atime={access_time}, mtime={modified_time}")
    except Exception as e:
        print(f"Failed to update timestamp: {e}")


def insert_file(local_file, destination_path, access_time, modified_time, password):
    if not os.path.exists(local_file):
        print(f"Error: {local_file} does not exist.")
        return
    
    run_sudo_command(f"mkdir -p '{os.path.dirname(destination_path)}'", password)
    run_sudo_command(f"cp '{local_file}' '{destination_path}'", password)
    set_file_timestamp(destination_path, access_time, modified_time, password)
    print(f"Inserted {local_file} -> {destination_path}")


def insert_files_into_dd(image_file, file_operations, mount_point="/mnt/linux_data"):
    """
    Insert multiple files into a disk image.

    Args:
        image_file (str): Path to the .dd image.
        file_operations (list of dict): Each dict has keys: 'local_path', 'target_path', 'access_time', 'modified_time'.
        mount_point (str): Where to mount the image.
    """
    if not os.path.exists(image_file):
        raise FileNotFoundError(f"Disk image not found: {image_file}")

    password = getpass.getpass("Enter your sudo password: ")

    print("Mounting disk image...")
    mount_image(image_file, mount_point, password)

    try:
        for op in file_operations:
            local_file = op['local_path']
            relative_target = op['target_path'].lstrip("/")
            full_destination = os.path.join(mount_point, relative_target)

            insert_file(local_file, full_destination, op['access_time'], op['modified_time'], password)
    finally:
        print("Unmounting disk image...")
        unmount_image(mount_point, password)


# Example usage:
# file_ops = [
#     {"local_path": "/path/to/file1.txt", "target_path": "/folder1/file1.txt", "access_time": "2025-04-17 12:00:00", "modified_time": "2025-04-17 12:30:00"},
#     {"local_path": "/path/to/file2.txt", "target_path": "/folder2/file2.txt", "access_time": "2025-04-17 13:00:00", "modified_time": "2025-04-17 13:30:00"}
# ]
# insert_files_into_dd("/path/to/image.dd", file_ops)
