#!/usr/bin/env python3
"""
upload_to_obs.py - Uploads image to Huawei Cloud Object Storage Service (OBS).
Reads credentials from environment variables:
- HWC_AK / HUAWEI_AK
- HWC_SK / HUAWEI_SK
- HWC_REGION / HUAWEI_REGION
- HWC_OBS_BUCKET / OBS_BUCKET
- HWC_OBS_ENDPOINT / OBS_ENDPOINT
Leverages official high-performance obsutil CLI with Python SDK fallback.
Compatible with Antigravity Agent Skill: ims-cloud-uploader.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time


def get_env_var(candidates, default=None, required=True):
    if isinstance(candidates, str):
        candidates = [candidates]
    for name in candidates:
        val = os.getenv(name)
        if val:
            return val
    if required and default is None:
        names_str = " or ".join(candidates)
        print(f"\n[CRITICAL] Missing required environment variable: {names_str}", file=sys.stderr)
        print("Define the variable in your shell or use the template:", file=sys.stderr)
        print(f"    export {candidates[0]}=\"your_value\"", file=sys.stderr)
        print("    source scripts/huawei_env.sh\n", file=sys.stderr)
        sys.exit(1)
    return default


def find_obsutil():
    workspace_bin = os.path.join(os.path.dirname(__file__), "..", "bin", "obsutil")
    if os.path.isfile(workspace_bin) and os.access(workspace_bin, os.X_OK):
        return os.path.abspath(workspace_bin)
    system_bin = shutil.which("obsutil")
    if system_bin:
        return system_bin
    return None


def upload_with_obsutil(obsutil_bin, local_file, bucket, endpoint, ak, sk, object_name):
    print(f"[*] Using official obsutil tool: {obsutil_bin}")
    
    cfg_cmd = [
        obsutil_bin, "config",
        f"-i={ak}",
        f"-k={sk}",
        f"-e={endpoint}"
    ]
    print("[*] Configuring obsutil credentials...")
    subprocess.run(cfg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    dest_uri = f"obs://{bucket}/{object_name}"
    print(f"\n[*] Starting transfer: {local_file}")
    print(f"[*] Destination: {dest_uri}")

    cp_cmd = [
        obsutil_bin, "cp",
        local_file,
        dest_uri,
        "-u",          # Resumable multipart
        "-vmd5",       # Validate MD5 hash
        "-j=5"         # Parallel workers
    ]

    start_time = time.time()
    subprocess.run(cp_cmd, check=True)
    duration = time.time() - start_time
    print(f"\n[OK] Transfer complete via obsutil in {duration:.1f}s!")
    return dest_uri


def upload_fallback_direct(local_file, bucket, endpoint, ak, sk, object_name):
    try:
        from obs import ObsClient
        print("[*] Found esdk-obs-python. Uploading via SDK...")
        obs_client = ObsClient(access_key_id=ak, secret_access_key=sk, server=endpoint)
        
        dest_uri = f"obs://{bucket}/{object_name}"
        print(f"[*] Transferring: {local_file} -> {dest_uri}")
        
        resp = obs_client.putFile(bucketName=bucket, objectKey=object_name, file_path=local_file)
        if resp.status < 300:
            print("[OK] SDK upload successful!")
            return dest_uri
        else:
            print(f"[ERROR] OBS response: status={resp.status}, code={resp.errorCode}, msg={resp.errorMessage}", file=sys.stderr)
            sys.exit(1)
    except ImportError:
        print("\n" + "="*70, file=sys.stderr)
        print("[WARNING] Neither 'obsutil' nor 'esdk-obs-python' is installed.", file=sys.stderr)
        print("To download obsutil automatically:", file=sys.stderr)
        print("    ./scripts/setup_prerequisites.sh", file=sys.stderr)
        print("Or install the Python SDK:", file=sys.stderr)
        print("    pip install esdk-obs-python", file=sys.stderr)
        print("="*70 + "\n", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Upload image to Huawei Cloud OBS bucket")
    parser.add_argument("--image", required=True, help="Local image file path")
    parser.add_argument("--bucket", default=None, help="Target OBS bucket name (or via HWC_OBS_BUCKET)")
    parser.add_argument("--endpoint", default=None, help="OBS endpoint URL (or via HWC_OBS_ENDPOINT)")
    parser.add_argument("--object-name", default=None, help="Remote object key (default: basename of image)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate parameters without uploading")

    args = parser.parse_args()

    local_path = os.path.abspath(args.image)
    if not os.path.exists(local_path):
        print(f"[ERROR] File not found: {local_path}", file=sys.stderr)
        sys.exit(1)

    ak = get_env_var(["HWC_AK", "HUAWEI_AK"])
    sk = get_env_var(["HWC_SK", "HUAWEI_SK"])
    
    endpoint = args.endpoint or get_env_var(["HWC_OBS_ENDPOINT", "OBS_ENDPOINT", "HUAWEI_OBS_ENDPOINT"], default="https://obs.sa-brazil-1.myhuaweicloud.com", required=False)
    
    derived_region = "sa-brazil-1"
    if "obs." in endpoint:
        try:
            derived_region = endpoint.split("obs.")[1].split(".myhuaweicloud")[0]
        except Exception:
            pass
            
    region = get_env_var(["HWC_REGION", "HUAWEI_REGION"], default=derived_region, required=False)
    bucket = args.bucket or get_env_var(["HWC_OBS_BUCKET", "OBS_BUCKET", "HUAWEI_OBS_BUCKET"])
    object_name = args.object_name or os.path.basename(local_path)

    image_url_param = f"{bucket}:{object_name}"

    print("\n=======================================================")
    print("[*] Huawei Cloud OBS Upload Parameters:")
    print(f"    Source: {local_path}")
    print(f"    Region: {region}")
    print(f"    Bucket: {bucket}")
    print(f"    Endpoint: {endpoint}")
    print(f"    Object Key: {object_name}")
    print(f"    IMS Identifier (image_url): {image_url_param}")
    print("=======================================================")

    if args.dry_run:
        print("[DRY-RUN] Parameters validated successfully. No data sent.")
        return

    obsutil_bin = find_obsutil()
    if obsutil_bin:
        dest_uri = upload_with_obsutil(obsutil_bin, local_path, bucket, endpoint, ak, sk, object_name)
    else:
        dest_uri = upload_fallback_direct(local_path, bucket, endpoint, ak, sk, object_name)

    manifest = {
        "status": "uploaded",
        "local_file": local_path,
        "region": region,
        "obs_bucket": bucket,
        "obs_endpoint": endpoint,
        "object_name": object_name,
        "obs_uri": dest_uri,
        "ims_image_url": image_url_param,
        "timestamp": int(time.time())
    }
    manifest_path = local_path + ".obs_upload.json"
    with open(manifest_path, 'w') as mf:
        json.dump(manifest, mf, indent=2)

    print(f"\n[SUCCESS] Upload complete!")
    print(f"          OBS URI: {dest_uri}")
    print(f"          IMS URL Parameter: {image_url_param}")
    print(f"          Manifest: {manifest_path}\n")


if __name__ == "__main__":
    main()
