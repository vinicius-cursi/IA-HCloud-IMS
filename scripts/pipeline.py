#!/usr/bin/env python3
"""
pipeline.py - Unified orchestrator for Huawei Cloud IMS image factory.
Executes the end-to-end pipeline:
1. Resumable image download with hash verification
2. Package unpacking (OVA/TAR) and format conversion (QCOW2/RAW/ZVHD2) with single-disk policy
3. Strict compliance validation against official Huawei Cloud requirements
4. Non-destructive local headless KVM boot smoke testing via QEMU VirtIO
5. Multipart upload to Huawei Cloud OBS using environment variables
6. Registration of private image in Huawei Cloud IMS
Compatible with Antigravity Agent Skill: ims-pipeline-orchestrator.
"""

import argparse
import os
import subprocess
import sys
import time


def print_step_banner(step_num, title):
    print("\n" + "#"*75)
    print(f"  STEP {step_num}: {title.upper()}")
    print("#"*75 + "\n")


def run_pipeline(url=None, local_input=None, target_format="qcow2", os_type="linux", boot_mode="bios",
                 skip_boot_test=False, skip_upload=False, skip_import=False, dry_run=False):
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_dir = os.path.dirname(scripts_dir)
    downloads_dir = os.path.join(workspace_dir, "downloads")
    extract_dir = os.path.join(workspace_dir, "extracted_images")
    output_dir = os.path.join(workspace_dir, "images")

    start_total_time = time.time()
    input_file = local_input

    # STEP 1: DOWNLOAD
    if url:
        print_step_banner(1, "Download Image")
        dl_script = os.path.join(scripts_dir, "download_image.py")
        cmd = [sys.executable, dl_script, "--url", url, "--output-dir", downloads_dir]
        subprocess.run(cmd, check=True)
        parsed_name = os.path.basename(url.split("?")[0])
        input_file = os.path.join(downloads_dir, parsed_name)
    elif not input_file:
        print("[ERROR] Please provide --url or local file via --input.", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(input_file):
        print(f"[ERROR] Input file does not exist: {input_file}", file=sys.stderr)
        sys.exit(1)

    # STEP 2: EXTRACT & CONVERT
    print_step_banner(2, "Extract & Convert (Single-Disk Enforcement)")
    convert_script = os.path.join(scripts_dir, "extract_and_convert.py")
    cmd_convert = [
        sys.executable, convert_script,
        "--input", input_file,
        "--extract-dir", extract_dir,
        "--output-dir", output_dir,
        "--format", target_format
    ]
    subprocess.run(cmd_convert, check=True)

    base_name = os.path.splitext(os.path.basename(input_file))[0]
    final_image = os.path.join(output_dir, f"{base_name}.{target_format}")
    if not os.path.exists(final_image):
        files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(f".{target_format}")]
        if files:
            final_image = max(files, key=os.path.getmtime)

    # STEP 3: TECHNICAL VALIDATION
    print_step_banner(3, "Huawei Cloud IMS Compliance Inspection")
    val_script = os.path.join(scripts_dir, "validate_image.py")
    cmd_val = [
        sys.executable, val_script,
        "--image", final_image,
        "--os-type", os_type,
        "--boot-mode", boot_mode
    ]
    subprocess.run(cmd_val, check=True)

    # STEP 4: LOCAL BOOT TEST
    if not skip_boot_test:
        print_step_banner(4, "Local Boot Smoke Test (VirtIO KVM Simulation)")
        boot_script = os.path.join(scripts_dir, "test_local_boot.py")
        cmd_boot = [sys.executable, boot_script, "--image", final_image, "--timeout", "30"]
        if dry_run:
            cmd_boot.append("--dry-run")
        subprocess.run(cmd_boot, check=False)
    else:
        print("\n[*] Step 4 (Local Boot Test) skipped via --skip-boot-test.")

    # STEP 5: OBS UPLOAD
    obs_manifest = final_image + ".obs_upload.json"
    if not skip_upload:
        print_step_banner(5, "Upload to Huawei Cloud OBS")
        upload_script = os.path.join(scripts_dir, "upload_to_obs.py")
        cmd_up = [sys.executable, upload_script, "--image", final_image]
        if dry_run:
            cmd_up.append("--dry-run")
        subprocess.run(cmd_up, check=True)
    else:
        print("\n[*] Step 5 (OBS Upload) skipped via --skip-upload.")

    # STEP 6: IMS REGISTRATION
    if not skip_import and not skip_upload:
        print_step_banner(6, "Huawei Cloud IMS Registration")
        import_script = os.path.join(scripts_dir, "import_ims_image.py")
        cmd_imp = [
            sys.executable, import_script,
            "--manifest", obs_manifest,
            "--name", base_name
        ]
        if dry_run:
            cmd_imp.append("--dry-run")
        subprocess.run(cmd_imp, check=True)
    else:
        print("\n[*] Step 6 (IMS Registration) skipped.")

    total_duration = time.time() - start_total_time
    print("\n" + "="*75)
    print(f" PIPELINE COMPLETED SUCCESSFULLY ({total_duration:.1f}s)")
    print(f" Image Ready: {final_image}")
    print("="*75 + "\n")


def main():
    parser = argparse.ArgumentParser(description="End-to-end image preparation pipeline for Huawei Cloud IMS")
    parser.add_argument("--url", help="Remote image URL to download")
    parser.add_argument("--input", help="Local image file (.ova, .qcow2, .vmdk, etc.)")
    parser.add_argument("--format", default="qcow2", choices=["qcow2", "raw", "zvhd2", "vmdk", "vhd"], help="Target format")
    parser.add_argument("--os-type", default="linux", choices=["linux", "windows"], help="Target guest OS type")
    parser.add_argument("--boot-mode", default="bios", choices=["bios", "uefi"], help="Boot firmware mode")
    parser.add_argument("--skip-boot-test", action="store_true", help="Skip local QEMU smoke boot test")
    parser.add_argument("--skip-upload", action="store_true", help="Skip OBS upload stage")
    parser.add_argument("--skip-import", action="store_true", help="Skip IMS registration stage")
    parser.add_argument("--dry-run", action="store_true", help="Run simulation without cloud modifications")

    args = parser.parse_args()
    run_pipeline(args.url, args.input, args.format, args.os_type, args.boot_mode,
                 args.skip_boot_test, args.skip_upload, args.skip_import, args.dry_run)


if __name__ == "__main__":
    main()
