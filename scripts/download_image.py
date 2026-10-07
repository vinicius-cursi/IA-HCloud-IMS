#!/usr/bin/env python3
"""
download_image.py - Resumable image downloader with SHA-256/MD5 validation.
Compatible with Antigravity Agent Skill: ims-downloader.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from urllib.parse import urlparse, unquote
import requests


def format_bytes(bytes_num):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_num < 1024.0:
            return f"{bytes_num:3.2f} {unit}"
        bytes_num /= 1024.0
    return f"{bytes_num:.2f} PB"


def calculate_hash(filepath, algorithm='sha256'):
    h = hashlib.new(algorithm)
    with open(filepath, 'rb') as f:
        while chunk := f.read(1024 * 1024 * 4):  # 4MB chunks
            h.update(chunk)
    return h.hexdigest().lower()


def download_file(url, target_dir, custom_filename=None, expected_hash=None, hash_algo='sha256'):
    os.makedirs(target_dir, exist_ok=True)
    
    if custom_filename:
        filename = custom_filename
    else:
        parsed_url = urlparse(url)
        filename = os.path.basename(unquote(parsed_url.path))
        if not filename or filename == '/':
            filename = f"image_download_{int(time.time())}.img"

    target_path = os.path.join(target_dir, filename)
    part_path = target_path + ".part"

    print(f"\n=======================================================")
    print(f"[*] Starting download: {filename}")
    print(f"[*] URL: {url}")
    print(f"[*] Target: {target_path}")
    print(f"=======================================================\n")

    headers = {}
    resume_byte_pos = 0

    if os.path.exists(part_path):
        resume_byte_pos = os.path.getsize(part_path)
        headers['Range'] = f'bytes={resume_byte_pos}-'
        print(f"[*] Resuming partial download from {format_bytes(resume_byte_pos)}...")

    start_time = time.time()
    
    # Use wget -c if available for high resilience and robust IPv4 fallback
    wget_bin = shutil.which("wget")
    if wget_bin:
        print(f"[*] Using '{wget_bin} -c' for transfer...")
        cmd = [wget_bin, "-c", "--show-progress", "-O", target_path, url]
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] wget failed: {e}", file=sys.stderr)
            return False, None
    else:
        try:
            response = requests.get(url, headers=headers, stream=True, timeout=(30, 300))
            if response.status_code == 200 and resume_byte_pos > 0:
                print("[!] Server does not support byte ranges. Restarting from byte 0...")
                resume_byte_pos = 0
                open_mode = 'wb'
            elif response.status_code == 206:
                open_mode = 'ab'
            elif response.status_code == 200:
                open_mode = 'wb'
            elif response.status_code == 416:
                print("[*] Partial file is already complete.")
                os.rename(part_path, target_path)
                response = None
            else:
                response.raise_for_status()

            if response is not None:
                content_length = response.headers.get('content-length')
                total_size = int(content_length) + resume_byte_pos if content_length else None
                downloaded = resume_byte_pos

                with open(part_path, open_mode) as f:
                    last_print_time = time.time()
                    bytes_since_last = 0
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            bytes_since_last += len(chunk)
                            
                            curr_time = time.time()
                            if curr_time - last_print_time >= 1.0 or (total_size and downloaded == total_size):
                                speed = bytes_since_last / (curr_time - last_print_time) if curr_time > last_print_time else 0
                                eta_str = ""
                                percent_str = ""
                                if total_size:
                                    percent = (downloaded / total_size) * 100
                                    remaining_bytes = total_size - downloaded
                                    eta = remaining_bytes / speed if speed > 0 else 0
                                    eta_str = f" | ETA: {int(eta)}s"
                                    percent_str = f"{percent:5.1f}% | "
                                
                                print(f"\rProgress: {percent_str}{format_bytes(downloaded)} / {format_bytes(total_size) if total_size else '???'} "
                                      f"| Speed: {format_bytes(speed)}/s{eta_str}", end='', flush=True)
                                
                                last_print_time = curr_time
                                bytes_since_last = 0

                print()
                os.rename(part_path, target_path)

        except Exception as e:
            print(f"\n[ERROR] Download failure: {e}", file=sys.stderr)
            return False, None

    duration = time.time() - start_time
    file_size = os.path.getsize(target_path)
    print(f"\n[OK] Transfer finished in {duration:.1f}s. Final file size: {format_bytes(file_size)}")

    # Hash calculation & verification
    calculated_hash = None
    print(f"[*] Calculating {hash_algo.upper()}...")
    calculated_hash = calculate_hash(target_path, hash_algo)
    print(f"[*] {hash_algo.upper()}: {calculated_hash}")
    
    if expected_hash:
        if calculated_hash.lower() == expected_hash.strip().lower():
            print(f"[OK] Checksum match confirmed.")
        else:
            print(f"[ERROR] Checksum mismatch! Expected: {expected_hash}, Actual: {calculated_hash}", file=sys.stderr)
            return False, target_path

    # Save manifest
    manifest = {
        "status": "success",
        "url": url,
        "filename": filename,
        "local_path": os.path.abspath(target_path),
        "size_bytes": file_size,
        "size_human": format_bytes(file_size),
        "hash_algo": hash_algo,
        "hash_value": calculated_hash,
        "timestamp": int(time.time())
    }
    manifest_path = target_path + ".json"
    with open(manifest_path, 'w') as mf:
        json.dump(manifest, mf, indent=2)

    print(f"[*] Manifest written to: {manifest_path}")
    return True, os.path.abspath(target_path)


def main():
    parser = argparse.ArgumentParser(description="Image downloader for Huawei Cloud IMS pipeline")
    parser.add_argument("--url", required=True, help="Remote image URL")
    parser.add_argument("--output-dir", default="downloads", help="Destination folder (default: downloads)")
    parser.add_argument("--filename", default=None, help="Custom filename override")
    parser.add_argument("--checksum", default=None, help="Expected hash for verification")
    parser.add_argument("--algo", default="sha256", choices=["sha256", "sha1", "md5"], help="Hash algorithm")
    
    args = parser.parse_args()
    success, filepath = download_file(args.url, args.output_dir, args.filename, args.checksum, args.algo)
    if not success:
        sys.exit(1)
    print(f"\n[SUCCESS] Image ready: {filepath}")


if __name__ == "__main__":
    main()
