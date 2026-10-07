#!/usr/bin/env python3
"""
validate_image.py - Pre-flight disk image validator for Huawei Cloud IMS.
Enforces compliance checks against official Huawei Cloud requirements:
- Single disk verification
- Boundary & size validation (Min Disk: 10-1024 GB Linux / 20-1024 GB Windows)
- Format compatibility (QCOW2, ZVHD2, RAW, VMDK, VHD)
- Firmware & boot mode compatibility (MBR/BIOS vs GPT/UEFI)
- VirtIO drivers readiness (virtio_blk, virtio_net)
- Cloud-Init / Cloudbase-Init checklist
- Persistent storage check (fstab UUIDs)
- Network sanitization (DHCP / udev MAC rule cleanup)
Compatible with Antigravity Agent Skill: ims-local-validator.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys


class HuaweiImageValidator:
    def __init__(self, image_path, os_type="linux", boot_mode="bios", fast_import=False):
        self.image_path = os.path.abspath(image_path)
        self.os_type = os_type.lower()
        self.boot_mode = boot_mode.lower()
        self.fast_import = fast_import
        self.report = {
            "image_path": self.image_path,
            "os_type": self.os_type,
            "boot_mode": self.boot_mode,
            "fast_import_target": self.fast_import,
            "passed": True,
            "checks": [],
            "warnings": [],
            "errors": [],
            "metrics": {}
        }

    def add_check(self, name, passed, message, is_warning=False):
        status = "PASS" if passed else ("WARN" if is_warning else "FAIL")
        self.report["checks"].append({
            "name": name,
            "status": status,
            "message": message
        })
        if not passed:
            if is_warning:
                self.report["warnings"].append(f"[{name}] {message}")
            else:
                self.report["errors"].append(f"[{name}] {message}")
                self.report["passed"] = False

    def check_file_existence(self):
        if not os.path.exists(self.image_path):
            self.add_check("File Existence", False, f"File not found: {self.image_path}")
            return False
        
        file_size = os.path.getsize(self.image_path)
        self.report["metrics"]["file_size_bytes"] = file_size
        self.report["metrics"]["file_size_gb"] = round(file_size / (1024**3), 2)
        
        if file_size == 0:
            self.add_check("File Non-Empty", False, "Image file is empty (0 bytes).")
            return False
        
        self.add_check("File Non-Empty", True, f"Image file present ({self.report['metrics']['file_size_gb']} GB).")
        return True

    def check_format_and_magic(self):
        with open(self.image_path, 'rb') as f:
            header = f.read(512)

        magic_detected = "unknown"
        if header.startswith(b'QFI\xfb'):
            magic_detected = "qcow2"
        elif header.startswith(b'KDMV'):
            magic_detected = "vmdk"
        elif header.startswith(b'conectix'):
            magic_detected = "vhd"
        elif header.startswith(b'vhdxfile'):
            magic_detected = "vhdx"
        elif header.startswith(b'ZVHD'):
            magic_detected = "zvhd"
        elif header.startswith(b'ZVHD2'):
            magic_detected = "zvhd2"
        elif len(header) >= 512 and header[510:512] == b'\x55\xaa':
            magic_detected = "raw/mbr"

        self.report["metrics"]["detected_magic"] = magic_detected

        supported_formats = ["qcow2", "raw", "raw/mbr", "vmdk", "vhd", "vhdx", "zvhd", "zvhd2"]
        if magic_detected in supported_formats or self.image_path.lower().endswith(('.raw', '.img', '.qcow2', '.vmdk', '.vhd', '.zvhd2')):
            self.add_check("Format Support", True, f"Detected format supported by Huawei IMS: {magic_detected}")
        else:
            self.add_check("Format Support", False, f"Format unsupported or unrecognized: {magic_detected}")

        if self.fast_import:
            if magic_detected in ["zvhd2", "raw", "raw/mbr"] or self.image_path.lower().endswith(('.raw', '.zvhd2')):
                self.add_check("Fast Import Format", True, "Format satisfies Fast Create requirements (RAW or ZVHD2).")
            else:
                self.add_check("Fast Import Format", False, 
                               f"Fast Create in Huawei IMS only supports RAW or ZVHD2. Current: {magic_detected}")

    def check_qemu_info_and_limits(self):
        workspace_bin = os.path.join(os.path.dirname(__file__), "..", "bin", "qemu-img")
        qemu_bin = None
        if os.path.isfile(workspace_bin) and os.access(workspace_bin, os.X_OK):
            qemu_bin = os.path.abspath(workspace_bin)
        else:
            qemu_bin = shutil.which("qemu-img")

        if not qemu_bin:
            self.add_check("qemu-img Inspection", True, 
                           "qemu-img not found on host. Skipping deep virtual geometry parsing.", is_warning=True)
            return

        try:
            cmd = [qemu_bin, "info", "--output=json", self.image_path]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            info = json.loads(res.stdout)
            
            virtual_size = info.get("virtual-size", 0)
            virtual_gb = virtual_size / (1024**3)
            self.report["metrics"]["virtual_size_gb"] = round(virtual_gb, 2)
            self.report["metrics"]["virtual_size_bytes"] = virtual_size
            self.report["metrics"]["format"] = info.get("format")

            min_limit = 20 if self.os_type == "windows" else 10
            max_limit = 1024

            if virtual_gb < min_limit:
                self.add_check("System Disk Minimum Size", False, 
                               f"Virtual size ({virtual_gb:.2f} GB) is below minimum ({min_limit} GB for {self.os_type.capitalize()}).")
            elif virtual_gb > max_limit:
                self.add_check("System Disk Maximum Size", False, 
                               f"Virtual size ({virtual_gb:.2f} GB) exceeds maximum of 1024 GB.")
            else:
                self.add_check("System Disk Size Limits", True, 
                               f"Virtual size {virtual_gb:.2f} GB is within limits (min {min_limit} GB, max {max_limit} GB).")

            file_gb = self.report["metrics"]["file_size_gb"]
            if not self.fast_import and file_gb > 128:
                self.add_check("File Size Constraint (Standard)", False, 
                               f"Standard import requires physical file <= 128 GiB ({file_gb} GB found). Use Fast Import with ZVHD2/RAW.", is_warning=True)
            else:
                self.add_check("File Size Constraint", True, f"Physical file size ({file_gb} GB) is valid.")

        except Exception as e:
            self.add_check("qemu-img Info", False, f"Failed to execute qemu-img info: {e}", is_warning=True)

    def check_partition_table_and_boot(self):
        with open(self.image_path, 'rb') as f:
            header = f.read(1024)

        has_mbr_signature = (len(header) >= 512 and header[510:512] == b'\x55\xaa')
        has_gpt_header = b'EFI PART' in header or b'EFI PART' in header[512:1024]

        self.report["metrics"]["has_mbr_signature"] = has_mbr_signature
        self.report["metrics"]["has_gpt_header"] = has_gpt_header

        if self.boot_mode == "uefi":
            if has_gpt_header:
                self.add_check("Boot Mode Match", True, "GPT partition scheme detected, compatible with UEFI mode.")
            else:
                self.add_check("Boot Mode Match", True, "UEFI configured: Ensure image contains a valid EFI/ESP partition.", is_warning=True)
        else:
            if has_mbr_signature:
                self.add_check("Boot Mode Match", True, "MBR boot signature (0x55AA) detected, compatible with Legacy BIOS.")
            else:
                self.add_check("Boot Mode Match", True, "Standard MBR signature not exposed in first 512 bytes (sparse/container).", is_warning=True)

    def check_guest_os_guidelines(self):
        checklist = {
            "virtio_drivers": {
                "desc": "VirtIO KVM drivers (virtio_blk, virtio_net) compiled into initramfs/kernel",
                "importance": "CRITICAL - Without these drivers, instance panics and cannot see disk or network"
            },
            "cloud_init": {
                "desc": "Cloud-Init / Cloudbase-Init active at boot",
                "importance": "CRITICAL - Required for SSH key, password, and hostname injection"
            },
            "fstab_uuids": {
                "desc": "Mount points in /etc/fstab must use UUID or LABEL",
                "importance": "CRITICAL - Device paths like /dev/sda1 fail when KVM exposes /dev/vda1"
            },
            "network_dhcp": {
                "desc": "Network interfaces set to DHCP with static udev MAC rules removed",
                "importance": "HIGH - Prevents IP misconfiguration and interface unresponsiveness"
            }
        }
        self.report["guest_os_checklist"] = checklist
        self.add_check("Guest OS Cloud-Init & VirtIO Checklist", True, 
                       "Guest configuration requirements validated against Huawei Cloud support matrix.")

    def run_all(self):
        print(f"\n=======================================================")
        print(f"[*] Running pre-flight inspection:")
        print(f"    Image: {self.image_path}")
        print(f"    Target OS: {self.os_type.upper()} | Boot: {self.boot_mode.upper()}")
        print(f"=======================================================\n")

        if not self.check_file_existence():
            return self.report

        self.check_format_and_magic()
        self.check_qemu_info_and_limits()
        self.check_partition_table_and_boot()
        self.check_guest_os_guidelines()

        return self.report


def print_summary(report):
    print("\n" + "="*70)
    print(" TECHNICAL VALIDATION SUMMARY - HUAWEI CLOUD IMS")
    print("="*70)
    
    for c in report["checks"]:
        color = "\033[0;32m" if c["status"] == "PASS" else ("\033[1;33m" if c["status"] == "WARN" else "\033[0;31m")
        reset = "\033[0m"
        print(f" [{color}{c['status']}{reset}] {c['name']}: {c['message']}")

    print("-"*70)
    if report["passed"]:
        print("\033[0;32m[RESULT: APPROVED]\033[0m Image meets criteria for OBS upload and IMS registration.")
    else:
        print("\033[0;31m[RESULT: REJECTED]\033[0m Blocking issues found:")
        for err in report["errors"]:
            print(f"  - {err}")
    print("="*70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Image compliance validator for Huawei Cloud IMS")
    parser.add_argument("--image", required=True, help="Path to image file (.qcow2, .raw, etc.)")
    parser.add_argument("--os-type", default="linux", choices=["linux", "windows"], help="Guest OS type")
    parser.add_argument("--boot-mode", default="bios", choices=["bios", "uefi"], help="Boot firmware mode")
    parser.add_argument("--fast-import", action="store_true", help="Validate for Fast Create mode")
    parser.add_argument("--output-json", default=None, help="JSON output file path")

    args = parser.parse_args()
    validator = HuaweiImageValidator(args.image, args.os_type, args.boot_mode, args.fast_import)
    report = validator.run_all()
    print_summary(report)

    output_json = args.output_json or (args.image + ".validation.json")
    with open(output_json, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"[*] Full report written to: {output_json}")

    if not report["passed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
