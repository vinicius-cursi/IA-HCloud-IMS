# Wiki & Architecture Reference

Operational documentation for the **Huawei Cloud IMS Image Factory** workspace.

---

## 1. Project Goal
Provide a reliable, automated pipeline to ingest, convert, validate, and upload Linux and Windows virtual machine disk images to **Huawei Cloud Image Management Service (IMS)** and **Object Storage Service (OBS)** in strict compliance with Huawei Cloud platform requirements.

---

## 2. Workspace Organization

```text
IMS_Huawei_Image/
├── .agents/                      # Antigravity agent configuration & skills
│   ├── rules/                    # Workspace rules
│   │   └── huawei_ims_rules.md
│   └── skills/                   # Modular runbooks & skills
│       ├── ims-downloader/
│       ├── ims-extractor-converter/
│       ├── ims-local-validator/
│       ├── ims-cloud-uploader/
│       ├── ims-cloud-importer/
│       └── ims-pipeline-orchestrator/
├── AGENTS.md                     # Senior Cloud Engineer instructions
├── GEMINI.md                     # Context directives for agents
├── downloads/                    # Inbound image files (.ova, .qcow2, .vmdk)
├── extracted_images/             # Intermediate extraction directory for multi-disk packages
├── images/                       # Converted production-ready images & JSON manifests
├── scripts/                      # Automation CLI tools
│   ├── setup_prerequisites.sh    # Environment setup & dependency bootstrap
│   ├── download_image.py         # Resumable downloader with hash check
│   ├── extract_and_convert.py    # OVA extractor & single-disk converter
│   ├── validate_image.py         # Static compliance inspection tool
│   ├── test_local_boot.py        # Local QEMU VirtIO headless boot tester
│   ├── upload_to_obs.py          # Parallel multipart OBS uploader
│   ├── import_ims_image.py       # IMS API registration client
│   ├── pipeline.py               # Unified end-to-end pipeline runner
│   └── huawei_env.sh.example     # Environment variables template
├── docs/                         # Official requirements & setup guides
│   ├── manual_portal_creation.md
│   ├── huawei_ims_specifications.md
│   ├── env_vars_guide.md
│   ├── guest_os_preparation_linux.md
│   ├── guest_os_preparation_windows.md
│   └── supported_image_matrix.md
└── wiki_guide/                   # Architecture, agent flow & runbooks
    ├── README.md
    ├── agent_workflow.md
    ├── local_testing_guide.md
    └── troubleshooting.md
```

---

## 3. Quickstart

### Step 1: Install Host Prerequisites
```bash
./scripts/setup_prerequisites.sh
```

### Step 2: Configure Environment Variables
```bash
cp scripts/huawei_env.sh.example scripts/huawei_env.sh
# Add your AK, SK, Bucket, and Region
source scripts/huawei_env.sh
```

### Step 3: Run the Pipeline
From a remote image URL:
```bash
python3 scripts/pipeline.py \
    --url "https://cloud-images.ubuntu.com/releases/22.04/release/ubuntu-22.04-server-cloudimg-amd64.img" \
    --format qcow2
```

From an existing local OVA/VMDK file:
```bash
python3 scripts/pipeline.py \
    --input "downloads/vmware_appliance.ova" \
    --format qcow2
```
