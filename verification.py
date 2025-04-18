import os
import hashlib
import tempfile
import shutil
import sys
import subprocess

def run_sudo_command(command, password):
    full_command = f"echo {password} | sudo -S {command}"
    result = subprocess.run(full_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {command}\n{result.stderr.decode()}")

def get_largest_partition_offset(image_file, password):
    command = f"fdisk -l {image_file}"
    full_command = f"echo {password} | sudo -S {command}"
    result = subprocess.run(full_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError("Failed to run fdisk to detect partition offset.")

    output = result.stdout.decode()
    offsets = []
    for line in output.splitlines():
        if image_file in line and line.strip().split()[0] != image_file:
            parts = line.split()
            try:
                start_sector = int(parts[1])
                sector_size = 512  # assume standard sector size
                offset = start_sector * sector_size
                offsets.append(offset)
            except (IndexError, ValueError):
                continue

    if offsets:
        return max(offsets)
    return None

def mount_image(image_file, mount_point, password):
    partition_offset = get_largest_partition_offset(image_file, password)
    if partition_offset is None:
        raise RuntimeError("Could not detect partition offset.")

    run_sudo_command(f"mkdir -p {mount_point}", password)
    mount_command = f"mount -o loop,offset={partition_offset} {image_file} {mount_point}"
    run_sudo_command(mount_command, password)

def unmount_image(mount_point, password):
    run_sudo_command(f"umount {mount_point}", password)

def compute_sha256(file_path):
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def verify_files(image_path, filelist_path, password):
    mount_dir = tempfile.mkdtemp()
    results = []

    try:
        mount_image(image_path, mount_dir, password)

        with open(filelist_path, "r") as f:
            for line in f:
                original_path = line.strip()
                relative_path = os.path.relpath(original_path, "/")
                mounted_path = os.path.join(mount_dir, relative_path)

                if os.path.exists(mounted_path):
                    sha256 = compute_sha256(mounted_path)
                    results.append(f"✅ {original_path} | SHA256: {sha256}")
                else:
                    results.append(f"❌ {original_path} | File not found")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        try:
            unmount_image(mount_dir, password)
        except Exception as e:
            print(f"Failed to unmount: {e}")
        shutil.rmtree(mount_dir)

    print("\n=== Verification Results ===")
    for r in results:
        print(r)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 verification.py image.dd file_paths.txt yourSudoPassword")
        sys.exit(1)

    image_path = sys.argv[1]
    filelist_path = sys.argv[2]
    sudo_password = sys.argv[3]

    verify_files(image_path, filelist_path, sudo_password)
