import subprocess
import os


def run_sudo_command(command, password):
    """Run a sudo command with password input."""
    # Create the full sudo command with the password passed through stdin
    full_command = f'echo {password} | sudo -S ' + ' '.join(command)

    try:
        subprocess.run(full_command, shell=True, check=True)
        print(f"Successfully ran command: {' '.join(command)}")
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        return False
    return True


def mount_image(image_path, mount_point, partition_offset=0, password=""):
    """Mount the .dd image to a specific mount point."""
    # Ensure the mount point exists
    if not os.path.exists(mount_point):
        os.makedirs(mount_point)

    # Try to mount with a specific offset (if needed)
    try:
        # If partition_offset is non-zero, mount with offset
        mount_command = ['mount', '-o', f'loop,offset={partition_offset}', image_path, mount_point]
        if partition_offset > 0:
            run_sudo_command(mount_command, password)
        else:
            mount_command = ['mount', '-o', 'loop', image_path, mount_point]
            run_sudo_command(mount_command, password)

        print(f"Image {image_path} mounted successfully to {mount_point}")
    except subprocess.CalledProcessError as e:
        print(f"Error mounting the image: {e}")
        return False
    return True


def unmount_image(mount_point, password=""):
    """Unmount the .dd image from the specified mount point."""
    try:
        unmount_command = ['umount', mount_point]
        run_sudo_command(unmount_command, password)
        print(f"Image unmounted successfully from {mount_point}")
    except subprocess.CalledProcessError as e:
        print(f"Error unmounting the image: {e}")
        return False
    return True


def main():
    image_path = "windows.dd"  # Path to your .dd image
    mount_point = "/mnt/windows"  # Directory to mount the .dd image
    password = "your_password_here"  # Replace with your sudo password

    # For Partition 2, starting at sector 104448, calculate the offset:
    partition_offset = 104448 * 512  # 104448 sectors * 512 bytes/sector

    # Mount the image
    if mount_image(image_path, mount_point, partition_offset, password):
        # Perform operations on the mounted image (e.g., insert a file)
        # After finishing operations, unmount the image
        if unmount_image(mount_point, password):
            print("Unmounted the partition successfully.")
        else:
            print("Failed to unmount the partition.")


if __name__ == "__main__":
    main()
