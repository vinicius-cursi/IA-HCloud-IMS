#!/usr/bin/env python3
"""
import_ims_image.py - Registers and imports private images in Huawei Cloud IMS.
Uses official Huawei Cloud REST API / Python SDK.
Reads credentials from environment variables:
- HWC_AK / HUAWEI_AK
- HWC_SK / HUAWEI_SK
- HWC_REGION / HUAWEI_REGION
- HWC_PROJECT_ID / HUAWEI_PROJECT_ID
Core API parameters:
- image_url: 'bucket_name:object_name' staged in OBS
- min_disk: minimum disk size in GB (10-1024 Linux / 20-1024 Windows)
- is_quick_import: boolean (true for RAW/ZVHD2 Fast Create)
- os_version: supported OS release identifier
Compatible with Antigravity Agent Skill: ims-cloud-importer.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone


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


def create_ims_request_body(name, image_url, min_disk, os_version, description, is_quick_import):
    body = {
        "name": name,
        "description": description or f"Imported via Antigravity IMS Automation on {datetime.now().isoformat()}",
        "image_url": image_url,
        "min_disk": int(min_disk),
        "os_version": os_version,
        "is_quick_import": bool(is_quick_import),
        "tags": ["automation:antigravity", "managed:ims-agent"]
    }
    return body


def register_image_via_sdk_or_mock(region, ak, sk, project_id, body, dry_run=False):
    ims_endpoint = f"https://ims.{region}.myhuaweicloud.com/v2/cloudimages/action"

    print("\n=======================================================")
    print("[*] Huawei Cloud IMS Request Specification:")
    print(f"    Endpoint: {ims_endpoint}")
    print(f"    Region: {region}")
    print(f"    Project ID: {project_id}")
    print(f"    Payload JSON:")
    print(json.dumps(body, indent=4))
    print("=======================================================\n")

    if dry_run:
        print("[DRY-RUN] Simulation successful. No requests sent to cloud API.")
        return "job-dry-run-success-001"

    try:
        from huaweicloudsdkcore.auth.credentials import BasicCredentials
        from huaweicloudsdkims.v2 import ImsClient, CreateImageRequest, CreateImageRequestBody

        credentials = BasicCredentials(ak, sk, project_id)
        client = ImsClient.new_builder() \
            .with_credentials(credentials) \
            .with_endpoint(f"https://ims.{region}.myhuaweicloud.com") \
            .build()

        request = CreateImageRequest()
        req_body = CreateImageRequestBody(
            name=body["name"],
            description=body["description"],
            image_url=body["image_url"],
            min_disk=body["min_disk"],
            os_version=body["os_version"],
            is_quick_import=body["is_quick_import"],
            tags=body["tags"]
        )
        request.body = req_body

        print("[*] Submitting image creation request via Huawei Cloud SDK...")
        response = client.create_image(request)
        job_id = response.job_id
        print(f"[OK] Asynchronous job created: {job_id}")
        return job_id

    except ImportError:
        print("\n" + "="*70)
        print("[INFO] 'huaweicloudsdkims' is not installed in the current environment.")
        print("To submit registration directly via Python SDK:")
        print("    pip install huaweicloudsdkims huaweicloudsdkcore")
        print("\nAlternatively, complete manual registration via the Huawei Cloud Console:")
        print("    1. Navigate to: https://console.huaweicloud.com/ims/")
        print("    2. Click 'Create Image' -> 'System Disk Image' -> 'Image File (OBS)'")
        print(f"    3. Select: {body['image_url']}")
        print(f"    4. Set Min Disk: {body['min_disk']} GB, OS: {body['os_version']}")
        print(f"    5. Follow guide in docs/manual_portal_creation.md")
        print("="*70 + "\n")
        return "manual-or-sdk-pending"


def main():
    parser = argparse.ArgumentParser(description="Image registration client for Huawei Cloud IMS")
    parser.add_argument("--name", default=None, help="Private image name in IMS")
    parser.add_argument("--image-url", default=None, help="OBS object path: 'bucket_name:file_name'")
    parser.add_argument("--manifest", default=None, help="Path to .obs_upload.json manifest")
    parser.add_argument("--min-disk", type=int, default=None, help="Minimum system disk in GB (e.g., 40)")
    parser.add_argument("--os-version", default="Ubuntu 22.04 server 64bit", help="Operating system release")
    parser.add_argument("--description", default="Imported via Antigravity IMS pipeline", help="Description")
    parser.add_argument("--quick-import", action="store_true", help="Enable Fast Create (RAW or ZVHD2)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate parameters without cloud call")

    args = parser.parse_args()

    image_url = args.image_url
    if args.manifest and os.path.exists(args.manifest):
        with open(args.manifest, 'r') as mf:
            mdata = json.load(mf)
            image_url = image_url or mdata.get("ims_image_url")

    image_url = image_url or os.getenv("IMS_IMAGE_URL")
    if not image_url:
        print("[ERROR] Please provide --image-url or --manifest from upload stage.", file=sys.stderr)
        sys.exit(1)

    ak = get_env_var(["HWC_AK", "HUAWEI_AK"])
    sk = get_env_var(["HWC_SK", "HUAWEI_SK"])
    region = get_env_var(["HWC_REGION", "HUAWEI_REGION"], default="sa-brazil-1", required=False)
    project_id = get_env_var(["HWC_PROJECT_ID", "HUAWEI_PROJECT_ID"], default="", required=False)

    image_name = args.name or os.getenv("IMS_IMAGE_NAME", f"img-ims-{int(time.time())}")
    min_disk = args.min_disk or int(os.getenv("IMS_MIN_DISK", 40))
    os_ver = args.os_version or os.getenv("IMS_OS_VERSION", "Ubuntu 22.04 server 64bit")
    is_quick = args.quick_import or (os.getenv("IMS_IS_QUICK_IMPORT", "false").lower() == "true")

    body = create_ims_request_body(image_name, image_url, min_disk, os_ver, args.description, is_quick)
    job_id = register_image_via_sdk_or_mock(region, ak, sk, project_id, body, args.dry_run)

    record = {
        "status": "registered",
        "job_id": job_id,
        "region": region,
        "ims_name": image_name,
        "image_url": image_url,
        "min_disk": min_disk,
        "os_version": os_ver,
        "is_quick_import": is_quick,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    rec_file = f"images/{image_name}.ims_registration.json"
    with open(rec_file, 'w') as rf:
        json.dump(record, rf, indent=2)

    print(f"[*] IMS registration manifest saved: {rec_file}")


if __name__ == "__main__":
    main()
