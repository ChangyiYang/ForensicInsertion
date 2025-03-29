import subprocess
import os
import getpass
import shutil
import re


# Function to execute commands with sudo privileges and password
def run_sudo_command(command):
    sudo_command = f"echo {password} | sudo -S {command}"
    process = subprocess.Popen(sudo_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        print(f"Error: {stderr.decode()}")
    else:
        print(stdout.decode())
        return stdout.decode()


# Function to detect the largest partition offset dynamically using partx
def get_largest_partition_offset(image_file):
    result = run_sudo_command(f"partx -b {image_file}")
    if not result:
        print(f"Error: {result.stderr.decode()}")
        return None

    partitions = []
    for line in result.splitlines():
        partition_regex = r'(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([a-f0-9\-]+)'
        match = re.search(partition_regex, line)
        if match:
            device = match.group(1)
            start = int(match.group(2))
            end = int(match.group(3))
            sectors = int(match.group(4))
            size = match.group(5)
            partitions.append((device, start, end, sectors, size))

    if not partitions:
        print("No partitions found.")
        return None

    largest_partition = max(partitions, key=lambda x: x[3])
    # print(f"Largest partition has offset {largest_partition[1]} (sectors) and size {largest_partition[4]}.")

    # Each sector ~ 512 bytes
    return largest_partition[1] * 512


# Function to mount the disk image using the largest partition offset
def mount_image(image_file):
    partition_offset = get_largest_partition_offset(image_file)

    if partition_offset is None:
        print("Error: Could not detect partition offset.")
        return

    # Construct the mount command dynamically
    mount_command = f"mount -o loop,offset={partition_offset} {image_file} /mnt/linux_data"
    run_sudo_command(mount_command)


# Function to unmount the disk image
def unmount_image():
    unmount_command = "umount /mnt/linux_data"
    run_sudo_command(unmount_command)


# Function to copy the local file into the mounted image
def insert_file_into_image(local_file, destination_path):
    if not os.path.exists(local_file):
        print(f"Error: {local_file} does not exist.")
        return

    # Copy the local file to the mounted directory
    run_sudo_command(f"cp {local_file} {destination_path}")
    print(f"File {local_file} copied to {destination_path}.")


if __name__ == "__main__":
    # Ask the user for their sudo password securely
    password = getpass.getpass("Enter your sudo password: ")

    # Path to the local file you want to insert
    local_file = "../files/capital1.png"  # Replace with your local file path
    mount_point = "/mnt/linux_data"
    destination_path = os.path.join(mount_point, os.path.basename(local_file))

    # Path to the .dd image file
    image_file = "linux.dd"  # Replace with the path to your .dd file

    # Mount the disk image
    print("Mounting the disk image...")
    mount_image(image_file)

    # Insert the local file into the mounted image
    print("Inserting the local file into the disk image...")
    insert_file_into_image(local_file, destination_path)

    # Unmount the disk image to save changes
    print("Unmounting the disk image...")
    unmount_image()