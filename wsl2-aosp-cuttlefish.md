Title: Running Cuttlefish virtual Android device on WSL2
Date: 2024-07-28

I needed to test out some patches for AOSP having only a Windows machine.

The [Goldfish Android Emulator](https://source.android.com/docs/setup/create/avd) was not enough; I had to use the [Cuttlefish virtual device](https://source.android.com/docs/devices/cuttlefish).

Using Cuttlefish in WSL2 wasn't officially supported at the time of writing.

### Details

I succeeded running it at the manifest hash [81e549decdee241c84d305c2ccc1bd2a73fc2eb2](https://android.googlesource.com/platform/manifest/+/81e549decdee241c84d305c2ccc1bd2a73fc2eb2) which was the latest main at the time of the attempt.

I followed [Download the Android source](https://source.android.com/docs/setup/download), then [Build Android](https://source.android.com/docs/setup/build/building).

I used the lunch target `aosp_cf_x86_64_phone-trunk_staging-eng`.

The I tried to run CVD using `launch_cvd`. It was not in my `$PATH`, but after running `envsetup` again, it got into my `$PATH`.

### Too many open files

The first error I had was:

```
[2024-07-27T18:08:00.444004939+00:00 ERROR devices::virtio::virtio_pci_device] failed to activate device: pcivirtio-sound failed to clone interrupt_evt: Too many open files (os error 24)
[2024-07-27T18:08:00.444020599+00:00 ERROR devices::virtio::virtio_pci_device] failed to activate device: pcivirtio-sound failed to clone interrupt_evt: Too many open files (os error 24)
[2024-07-27T18:08:00.444035299+00:00 ERROR devices::virtio::virtio_pci_device] failed to activate device: pcivirtio-sound failed to clone interrupt_evt: Too many open files (os error 24)
[2024-07-27T18:08:00.444043389+00:00 ERROR devices::virtio::virtio_pci_device] failed to activate device: pcivirtio-sound failed to clone interrupt_evt: Too many open files (os error 24)
[2024-07-27T18:08:00.444051219+00:00 ERROR devices::virtio::virtio_pci_device] failed to activate device: pcivirtio-sound failed to clone interrupt_evt: Too many open files (os error 24)
[2024-07-27T18:08:00.444065098+00:00 ERROR devices::virtio::virtio_pci_device] failed to activate device: pcivirtio-sound failed to clone interrupt_evt: Too many open files (os error 24)
```

Reason: my Debian in WSL2 had a very low `ulimit -n`, just 1024.

Fix: bump to 8192 with `ulimit -n 8192`.

### The architecture failed to build the vm

The second error I had was:

```
[2024-07-27T18:52:02.351063572+00:00 ERROR crosvm] exiting with error 1: the architecture failed to build the vm
Caused by:
    failed to create a PCI root hub: failed to create proxy device: Failed to configure tube: failed to receive packet: Connection reset by peer (os error 104)
Detected unexpected exit of monitored subprocess /home/line/aosp-main/out/host/linux-x86/bin/process_restarter
Subprocess /home/line/aosp-main/out/host/linux-x86/bin/process_restarter (27196) has exited with exit code 1
Stopping all monitored processes due to unexpected exit of critical process
```

Reason: [something going wrong with sandboxing?](https://groups.google.com/a/chromium.org/g/crosvm-dev/c/dSjhjDKZsLI)

Fix: invoke cvd with `launch_cvd --enable-sandbox=false`. I do not know the negative consequences of this.

### See the device UI

To see the CVD UI, I used the Web UI. I am not sure if it is documented anywhere. By default an httpd spins up on port 8443.

To get it from outside WSL2:

```
netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=8443 connectaddress=192.168.219.62 connectport=8443
```

The IP address above is the IP address of the WSL2 instance. May vary.

Optional, to access the Web UI from other nodes in the local network:

```
netsh advfirewall firewall add rule name=”Open Port 8443 for WSL2” dir=in action=allow protocol=TCP localport=8443
```

The UI is a bit finicky. It did not work in Safari for me. Rebooting CVD sometimes caused the picture to disappear. Reloading and reopening the device helped at times.
