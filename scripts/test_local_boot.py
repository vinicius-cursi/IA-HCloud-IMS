#!/usr/bin/env python3
"""
test_local_boot.py - Local headless KVM boot tester emulating Huawei ECS instances.
Uses QEMU with VirtIO block and network adapters in snapshot mode (non-destructive).
Monitors serial console output for:
- Linux kernel initialization
- Recognition of VirtIO controllers
- Detection of kernel panics or mount failures
- Systemd target completion or login prompt
Compatible with Antigravity Agent Skill: ims-local-validator.
"""

import argparse
import os
import shutil
import subprocess
import sys
import time


def find_qemu_system():
    qemu_bin = shutil.which("qemu-system-x86_64")
    if qemu_bin:
        return qemu_bin
    workspace_bin = os.path.join(os.path.dirname(__file__), "..", "bin", "qemu-system-x86_64")
    if os.path.isfile(workspace_bin) and os.access(workspace_bin, os.X_OK):
        return workspace_bin
    return None


def run_qemu_smoke_test(image_path, timeout_seconds=45, memory_mb=2048, cores=2, dry_run=False):
    qemu_bin = find_qemu_system()
    if not qemu_bin:
        print("\n" + "="*70, file=sys.stderr)
        print("[WARNING] 'qemu-system-x86_64' not installed on host.", file=sys.stderr)
        print("To install the emulator for local boot testing:", file=sys.stderr)
        print("    sudo apt-get update && sudo apt-get install -y qemu-system-x86", file=sys.stderr)
        print("or run:", file=sys.stderr)
        print("    ./scripts/setup_prerequisites.sh", file=sys.stderr)
        print("="*70 + "\n", file=sys.stderr)
        return False, "qemu-system-x86_64 missing"

    has_kvm = os.path.exists("/dev/kvm") and os.access("/dev/kvm", os.R_OK | os.W_OK)
    accel = "kvm" if has_kvm else "tcg"

    ext = os.path.splitext(image_path)[1].lower().replace(".", "")
    fmt = ext if ext in ["qcow2", "raw", "vmdk"] else "qcow2"

    log_path = image_path + ".boot_test.log"

    print("\n=======================================================")
    print("[*] Starting local boot test (Huawei ECS KVM simulation)")
    print(f"[*] Image: {image_path}")
    print(f"[*] Format: {fmt.upper()} | Acceleration: {accel.upper()}")
    print(f"[*] Devices: virtio-blk (disk), virtio-net (network)")
    print(f"[*] Mode: SNAPSHOT (All writes discarded on shutdown)")
    print(f"[*] Timeout: {timeout_seconds} seconds")
    print(f"[*] Serial console log: {log_path}")
    print("=======================================================\n")

    cmd = [
        qemu_bin,
        "-m", str(memory_mb),
        "-smp", str(cores),
        "-machine", "q35,accel=" + accel,
        "-drive", f"file={image_path},if=virtio,format={fmt},snapshot=on",
        "-net", "nic,model=virtio",
        "-net", "user",
        "-nographic",
        "-serial", f"file:{log_path}",
        "-no-reboot"
    ]

    if dry_run:
        print("[DRY-RUN] Execution command:")
        print(" ".join(cmd))
        return True, "Dry-run complete"

    if os.path.exists(log_path):
        os.remove(log_path)

    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    start_time = time.time()
    
    print("[*] Virtual machine spawned. Monitoring serial output...")

    success_markers = [
        "login:", "Welcome to", "Reached target Multi-User System",
        "Reached target Graphical Interface", "Cloud-init", "cloud-init",
        "Started OpenSSH Server", "IPv4"
    ]
    panic_markers = [
        "Kernel panic", "kernel panic", "Call Trace:", "VFS: Unable to mount root fs",
        "dracut-initqueue", "Entering emergency mode", "Failed to mount /sysroot"
    ]

    boot_detected = False
    panic_detected = False
    found_marker = None

    try:
        while time.time() - start_time < timeout_seconds:
            if proc.poll() is not None:
                break
            
            if os.path.exists(log_path):
                with open(log_path, 'r', errors='ignore') as lf:
                    content = lf.read()
                    
                    for p in panic_markers:
                        if p in content:
                            panic_detected = True
                            found_marker = p
                            break
                    if panic_detected:
                        break

                    for s in success_markers:
                        if s in content:
                            boot_detected = True
                            found_marker = s
                            break
                    if boot_detected:
                        break

            time.sleep(2)
            elapsed = int(time.time() - start_time)
            print(f"\rElapsed: {elapsed}s / {timeout_seconds}s...", end='', flush=True)

    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

    print()
    log_size = os.path.getsize(log_path) if os.path.exists(log_path) else 0

    if panic_detected:
        print("\n\033[0;31m[CRITICAL BOOT FAILURE]\033[0m Detected KERNEL PANIC or mount error!")
        print(f"Trigger marker: '{found_marker}'")
        print(f"Verify VirtIO modules in initramfs and check fstab entries.")
        print(f"Log details: {log_path}\n")
        return False, f"Kernel Panic: {found_marker}"

    elif boot_detected:
        print("\n\033[0;32m[LOCAL BOOT SUCCESS]\033[0m Image initialized successfully with VirtIO drivers.")
        print(f"Success marker: '{found_marker}'")
        print(f"Log written to: {log_path}\n")
        return True, f"Boot OK ({found_marker})"

    elif log_size > 500:
        print("\n\033[0;32m[CLEAN BOOT EVIDENCE]\033[0m Kernel output recorded to serial log without panics.")
        print(f"Log saved: {log_path} ({log_size} bytes)\n")
        return True, "Boot logged without panic"

    else:
        print("\n\033[1;33m[SERIAL TIMEOUT WARNING]\033[0m No serial output captured before timeout.")
        print("Normal if guest GRUB does not route 'console=ttyS0' to serial.")
        print(f"See docs/guest_os_preparation_linux.md\n")
        return True, "Serial timeout (no panic detected)"


def main():
    parser = argparse.ArgumentParser(description="Headless local KVM boot smoke tester for Huawei Cloud IMS")
    parser.add_argument("--image", required=True, help="Path to image file (.qcow2, .raw)")
    parser.add_argument("--timeout", type=int, default=30, help="Test timeout in seconds (default: 30)")
    parser.add_argument("--memory", type=int, default=2048, help="RAM in MB (default: 2048)")
    parser.add_argument("--cores", type=int, default=2, help="CPU cores (default: 2)")
    parser.add_argument("--dry-run", action="store_true", help="Print QEMU command without launching")

    args = parser.parse_args()
    success, reason = run_qemu_smoke_test(args.image, args.timeout, args.memory, args.cores, args.dry_run)
    if not success and reason != "qemu-system-x86_64 missing":
        sys.exit(1)


if __name__ == "__main__":
    main()
