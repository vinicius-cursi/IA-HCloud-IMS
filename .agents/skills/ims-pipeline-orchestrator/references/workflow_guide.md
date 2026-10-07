# Pipeline Workflow & Safeguards Guide

## End-to-End Execution Flow

```mermaid
flowchart TD
    A["Download Image from Internet"] -->|downloads/| B["Extract OVA / TAR Archive"]
    B --> C{"Check Disk Count"}
    C -->|Multiple Disks| D["Isolate Primary System Disk & Log Warning"]
    C -->|Single Disk| E["Convert to QCOW2 / ZVHD2"]
    D --> E
    E -->|imagem/| F["Static Validation (Huawei Cloud Limits)"]
    F --> G["Dynamic Local Smoke Boot (QEMU VirtIO)"]
    G --> H{"Boot Succeeded?"}
    H -->|No / Kernel Panic| I["Halt Pipeline & Output Diagnostics"]
    H -->|Yes / Clean Boot| J["Upload to Huawei Cloud OBS (obsutil)"]
    J --> K["Register Private Image in IMS"]
    K --> L["Image Ready for ECS Provisioning"]
```

## Reliability & Safety Guarantees
1. **Non-Destructive Testing**: Test boots execute using QEMU copy-on-write snapshots (`snapshot=on`). Master disk images are never modified.
2. **Early Failure Detection**: The pipeline halts immediately if a disk fails any IMS requirement (e.g., secondary attached disk, missing VirtIO drivers, or hardcoded fstab device names).
3. **Cloud Cost & Bandwidth Efficiency**: Zero OBS egress/ingress traffic is generated if an image fails local validation.
