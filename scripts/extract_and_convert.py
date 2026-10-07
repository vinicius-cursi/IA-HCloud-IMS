#!/usr/bin/env python3
"""
extract_and_convert.py - Archive unpacking and disk format converter.
Enforces official Huawei Cloud IMS single-disk and format constraints.
Compatible with Antigravity Agent Skill: ims-extractor-converter.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tarfile
import zipfile


def check_qemu_img():
    """Locates qemu-img from workspace bin/ or host PATH"""
    workspace_bin = os.path.join(os.path.dirname(__file__), "..", "bin", "qemu-img")
    if os.path.isfile(workspace_bin) and os.access(workspace_bin, os.X_OK):
        return os.path.abspath(workspace_bin)
    
    system_qemu = shutil.which("qemu-img")
    if system_qemu:
        return system_qemu
    return None


def check_qemu_img_hw():
    """Locates Huawei qemu-img-hw if present"""
    workspace_bin = os.path.join(os.path.dirname(__file__), "..", "bin", "qemu-img-hw")
    if os.path.isfile(workspace_bin) and os.access(workspace_bin, os.X_OK):
        return os.path.abspath(workspace_bin)
    return shutil.which("qemu-img-hw")


def get_image_info(qemu_bin, filepath):
    """Executes qemu-img info --output=json to inspect disk geometry"""
    try:
        cmd = [qemu_bin, "info", "--output=json", filepath]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"[WARNING] Failed to parse disk info with qemu-img: {e.stderr.strip()}", file=sys.stderr)
        return {}


def extract_archive(input_path, extract_dir):
    """Unpacks OVA (tar), tar.gz, or zip into scratch extraction directory"""
    os.makedirs(extract_dir, exist_ok=True)
    filename = os.path.basename(input_path).lower()
    
    print(f"\n[*] Unpacking archive: {input_path}")
    print(f"[*] Extraction target: {extract_dir}")

    if filename.endswith(".ova") or filename.endswith(".tar"):
        with tarfile.open(input_path, 'r') as tar:
            tar.extractall(path=extract_dir)
    elif filename.endswith(".tar.gz") or filename.endswith(".tgz"):
        with tarfile.open(input_path, 'r:gz') as tar:
            tar.extractall(path=extract_dir)
    elif filename.endswith(".zip"):
        with zipfile.ZipFile(input_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
    else:
        print(f"[*] File is not an archive container ({filename}). Processing as standalone disk.")
        return [input_path]

    extracted_files = []
    for root, _, files in os.walk(extract_dir):
        for f in files:
            extracted_files.append(os.path.join(root, f))
    
    print(f"[OK] Unpacked {len(extracted_files)} files.")
    return extracted_files


def find_disk_files(extracted_files):
    """Finds all virtual disk files (.vmdk, .vhd, .vhdx, .qcow2, .raw, .img, .vdi, .qed)"""
    valid_exts = ('.vmdk', '.vhd', '.vhdx', '.qcow2', '.raw', '.img', '.vdi', '.qed')
    disks = [f for f in extracted_files if f.lower().endswith(valid_exts)]
    return sorted(disks)


def convert_image(qemu_bin, source_file, target_file, target_format="qcow2", source_format=None, compress=False):
    """Converts disk using qemu-img or qemu-img-hw respecting Huawei flags"""
    os.makedirs(os.path.dirname(target_file), exist_ok=True)
    
    if target_format.lower() in ["zvhd", "zvhd2"]:
        hw_bin = check_qemu_img_hw()
        if not hw_bin:
            print(f"[ERROR] Converting to {target_format.upper()} requires Huawei 'qemu-img-hw'.", file=sys.stderr)
            print(f"        See docs/huawei_ims_specifications.md for details.", file=sys.stderr)
            sys.exit(1)
        qemu_bin = hw_bin

    cmd = [qemu_bin, "convert", "-p"]
    
    # Specific input flags per Huawei Cloud specifications
    if source_format:
        cmd.extend(["-f", source_format])
    elif source_file.lower().endswith(".vhd"):
        cmd.extend(["-f", "vpc"])  # Huawei requires vpc flag for VHD
    elif source_file.lower().endswith(".vhdx"):
        cmd.extend(["-f", "vhdx"])
    elif source_file.lower().endswith(".vmdk"):
        cmd.extend(["-f", "vmdk"])
    
    cmd.extend(["-O", target_format])

    if compress and target_format == "qcow2":
        cmd.append("-c")

    cmd.extend([source_file, target_file])

    print(f"\n[*] Running conversion:")
    print(f"    {' '.join(cmd)}")
    
    subprocess.run(cmd, check=True)
    print(f"[OK] Conversion completed: {target_file}")


def process_pipeline(input_path, extract_dir, output_dir, target_format="qcow2", disk_index=0, compress=False):
    qemu_bin = check_qemu_img()
    if not qemu_bin:
        print("\n" + "="*70, file=sys.stderr)
        print("[CRITICAL] 'qemu-img' not found!", file=sys.stderr)
        print("Install host prerequisites via:", file=sys.stderr)
        print("    sudo apt-get update && sudo apt-get install -y qemu-utils", file=sys.stderr)
        print("or run:", file=sys.stderr)
        print("    ./scripts/setup_prerequisites.sh", file=sys.stderr)
        print("="*70 + "\n", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Converter binary: {qemu_bin}")

    lower_input = input_path.lower()
    is_archive = lower_input.endswith(('.ova', '.tar', '.tar.gz', '.tgz', '.zip'))

    if is_archive:
        extracted = extract_archive(input_path, extract_dir)
        disk_files = find_disk_files(extracted)
    else:
        disk_files = [input_path]

    if not disk_files:
        print(f"[ERROR] No virtual disk files found!", file=sys.stderr)
        sys.exit(1)

    print(f"\n=======================================================")
    print(f"[*] Detected disks ({len(disk_files)} found):")
    for idx, d in enumerate(disk_files):
        size_mb = os.path.getsize(d) / (1024 * 1024)
        print(f"    [{idx}] {os.path.basename(d)} ({size_mb:.2f} MB)")
    print(f"=======================================================")

    # Enforce Huawei Cloud Single-Disk Rule
    if len(disk_files) > 1:
        print("\n" + "!"*70)
        print("[HUAWEI CLOUD IMS CONSTRAINT - SINGLE DISK]")
        print("Huawei Cloud IMS requires system disk images to contain exactly ONE disk.")
        print(f"Found {len(disk_files)} disks in package.")
        print(f"Selecting index [{disk_index}]: {disk_files[disk_index]} as SYSTEM DISK.")
        print("Remaining disks must be uploaded and imported separately as Data Disk Images.")
        print("!"*70 + "\n")

    selected_disk = disk_files[disk_index]
    disk_basename = os.path.splitext(os.path.basename(selected_disk))[0]
    
    target_filename = f"{disk_basename}.{target_format}"
    target_path = os.path.join(output_dir, target_filename)

    info_before = get_image_info(qemu_bin, selected_disk)
    src_format = info_before.get("format", None)
    virtual_size = info_before.get("virtual-size", 0)

    print(f"[*] Source format: {src_format}")
    print(f"[*] Virtual size: {virtual_size / (1024**3):.2f} GB")

    if src_format == target_format and not compress and not is_archive:
        print(f"[*] File is already in target format ({target_format}). Copying...")
        os.makedirs(output_dir, exist_ok=True)
        shutil.copy2(selected_disk, target_path)
    else:
        convert_image(qemu_bin, selected_disk, target_path, target_format, src_format, compress)

    info_after = get_image_info(qemu_bin, target_path)
    final_size = os.path.getsize(target_path)

    manifest = {
        "status": "ready_for_validation",
        "source_input": os.path.abspath(input_path),
        "source_disk": os.path.abspath(selected_disk),
        "total_disks_found": len(disk_files),
        "selected_disk_index": disk_index,
        "single_disk_compliant": True,
        "final_image_path": os.path.abspath(target_path),
        "target_format": target_format,
        "file_size_bytes": final_size,
        "file_size_gb": round(final_size / (1024**3), 2),
        "virtual_size_bytes": info_after.get("virtual-size", virtual_size),
        "virtual_size_gb": round(info_after.get("virtual-size", virtual_size) / (1024**3), 2),
        "qemu_info": info_after
    }

    manifest_file = target_path + ".json"
    with open(manifest_file, "w") as mf:
        json.dump(manifest, mf, indent=2)

    print(f"\n[SUCCESS] Converted image ready:")
    print(f"          Image: {target_path}")
    print(f"          Manifest: {manifest_file}")
    return os.path.abspath(target_path)


def main():
    parser = argparse.ArgumentParser(description="Image extraction and format converter for Huawei Cloud IMS")
    parser.add_argument("--input", required=True, help="Path to input image/archive (.ova, .vmdk, .qcow2, etc.)")
    parser.add_argument("--extract-dir", default="extracted_images", help="Scratch directory for extraction")
    parser.add_argument("--output-dir", default="images", help="Output directory for converted image")
    parser.add_argument("--format", default="qcow2", choices=["qcow2", "raw", "zvhd2", "vmdk", "vhd"], help="Target format (default: qcow2)")
    parser.add_argument("--disk-index", type=int, default=0, help="Disk index to isolate from multi-disk packages (default: 0)")
    parser.add_argument("--compress", action="store_true", help="Enable QCOW2 compression (-c)")

    args = parser.parse_args()
    process_pipeline(args.input, args.extract_dir, args.output_dir, args.format, args.disk_index, args.compress)


if __name__ == "__main__":
    main()
