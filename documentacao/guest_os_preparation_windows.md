# Windows Server Guest Preparation Guide for Huawei Cloud IMS

To import Windows Server (2012 R2, 2016, 2019, 2022, 2025) virtual disks into Huawei Cloud IMS, complete these configuration steps inside the VM before exporting the disk.

---

## 1. VirtIO Driver Installation

Huawei Cloud KVM requires VirtIO storage and network drivers. You can use standard Red Hat VirtIO Windows drivers or Huawei's `uvp-vmtools`.

1. Attach the VirtIO driver ISO to the VM.
2. Verify in Device Manager that the following devices have active VirtIO drivers:
   - **Network**: `Red Hat VirtIO Ethernet Adapter` (`NetKVM`)
   - **Storage**: `Red Hat VirtIO SCSI controller` (`viostor` and `vioscsi`)
   - **System Devices**: `VirtIO Balloon Driver` and `VirtIO Serial Driver`
3. Confirm that no device has a yellow warning icon.

---

## 2. Cloudbase-Init Installation

`Cloudbase-Init` is the Windows equivalent of Cloud-Init for OpenStack / Huawei Cloud environments:

1. Download the 64-bit installer for Cloudbase-Init.
2. Run the installation wizard:
   - Configuration options:
     - **Username**: `Administrator`
     - **Serial port for logging**: `COM1`
     - **Run Cloudbase-Init service as**: `Local System`
3. On the final screen:
   - Select **Run Sysprep** if you intend to generalize the SID for mass template deployment.
   - Select **Shutdown when finished**.

---

## 3. Windows SAN Storage Policy

Run in an administrative Command Prompt (`cmd.exe`) to ensure secondary EVS volumes attach and come online automatically:

```cmd
diskpart
san policy=onlineall
exit
```

---

## 4. Networking

1. Ensure the network adapter is set to **Obtain an IP address automatically (DHCP)** and **Obtain DNS server address automatically**.
2. Ensure Windows Firewall permits incoming RDP traffic on port 3389.

---

## 5. Exporting the Disk
Once the Windows VM shuts down, pass the resulting `.vmdk` or `.vhd` to `scripts/pipeline.py --os-type windows`.
