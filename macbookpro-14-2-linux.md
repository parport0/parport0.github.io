Title: Linux on Macbook Pro 14,2
Date: 2025-01-08

A quick look at <https://github.com/Dunedan/mbp-2016-linux> makes one lose hope, but it is way better than it looks at first.

This note is primarily for myself, if I have to reinstall Linux on this machine again. Low effort alert.

If you want to share some information with me, for example if something is wrong here, please email me.

I tried to install Debian using its installer, it froze... I had to install Ubuntu.

### T1 firmware

Do not uninstall Mac OS without backing up the EFI partition contents, or the T1/iBridge device will not be able to boot! The EFI partition has the chip's firmware.

You will be getting

```
Bus 001 Device 003: ID 05ac:1281 Apple, Inc. Apple Mobile Device [Recovery Mode]
```

instead of

```
Bus 001 Device 002: ID 05ac:8600 Apple, Inc. iBridge
```

(If you wiped Mac OS already, it's fine, you'll have to reinstall it, it is perfectly possible to reinstall)

You need to back up the `EFI/APPLE/` folder from the first partition on the NVMe. After you installed Linux, put the folder in the same place.

[Source](https://github.com/Dunedan/mbp-2016-linux/issues/52#issuecomment-364920804).

### Wi-Fi

From the [kernel bug 193121](https://bugzilla.kernel.org/show_bug.cgi?id=193121), download the attachment of *comment 74*,

change `boardflags3=0xC0000303` to `boardflags3=0x00000303`,

and save the file as `/lib/firmware/brcm/brcmfmac43602-pcie.txt`.

(I have it saved [here](brcmfmac43602-pcie.txt) also, already with the modification, just in case)

Then run `rmmod brcmfmac_wcc && rmmod brcmfmac && modprobe brcmfmac && modprobe brcmfmac_wcc`.

### Touchpad scroll in Firefox is too fast

It is a Firefox issue; in `about:config`, change `mousewheel.default.delta_multiplier_y` and `mousewheel.default.delta_multiplier_x` from 100 to 25-ish

[Firefox specificness source](https://discussion.fedoraproject.org/t/palm-rejection-scroll-speed/118505/3).

[Workaround source](https://askubuntu.com/questions/1447009/control-scrolling-speed-in-webpages-in-firefox).

### Palm rejection

Add to `/usr/share/libinput/50-system-apple.quirks`:

```
[Apple SPI Touchpad]
MatchName=*Apple SPI Touchpad*
ModelAppleTouchpad=1
AttrTouchSizeRange=50:30
AttrPalmSizeThreshold=1100

[Apple SPI Keyboard]
MatchName=*Apple SPI Keyboard*
AttrKeyboardIntegration=internal
```

and relogin.

[Source](https://gist.github.com/peterychuang/5cf9bf527bc26adef47d714c758a5509)

(I changed `AttrPalmSizeThreshold` from the suggested 800 to 1100 because I had weird behaviors when e.g. dragging windows or selecting text, which turned out to be palm detection kicking in too soon; it can be debugged with [libinput measure touch-size](https://wayland.freedesktop.org/libinput/doc/latest/touchpad-pressure-debugging.html#touchpad-touch-size-hwdb))

### Escape

[I found this on the mailing lists](https://lore.kernel.org/lkml/20190612083400.1015-1-ronald@innovation.ch/).

 It would benefit from someone addressing the round 2 review comments and resending these; I doubt I will have the time for it anytime soon. And first, the following unbind/probe issue needs to be resolved (unless it is my fault).

[I fixed this driver up a bit for 6.8.0 here](https://github.com/parport0/mbp-t1-touchbar-driver).

The unbind/probe issue is basically that I have to run these commands on boot:

```
sudo modprobe apple-ib-tb
sudo bash -c 'echo -n "1-3" > /sys/bus/usb/drivers/usb/unbind'
sudo bash -c 'echo -n 1-3 > /sys/bus/usb/drivers_probe'
```

I created a systemd oneshot service to run them `After=multi-user.target` and `WantedBy=graphical.target`.

Why are those unbind + probe needed? I needed them because otherwise the apple-ibridge driver is not expanding the `/sys/bus/usb/devices/1-3` device.

Maybe it is because the generic `usb` driver steals the device? There was a [patch to implement some "anti-stealing" functionality for the "generic" usb drivers](https://patchwork.kernel.org/project/linux-usb/patch/20200727104644.149873-3-hadess@hadess.net/), but I am not knowledgeable enough to say for sure why it does not work in this case. My suspicion is that the `apple-ibridge` driver needs to have a `usb_driver` entry as well? It only has a HID driver, which also kinda manages the `usb_device`.

But to be honest, even when I run the reprobe, and I get the touchbar to work, `/sys/bus/usb/devices/1-3/driver` still points to `bus/usb/drivers/usb`, so I don't understand at all what is going on there.

This driver is strange because it creates four virtual HID devices. If `lsusb -t` does not show four interfaces appearing on `05ac:8600`, then apple-ibridge.ko didn't do its job right.

If the devices are there, but the touchbar still doesn't light up, try to restart the laptop...

Why I didn't use the [roadrunner2 macbook12-spi-driver](https://github.com/roadrunner2/macbook12-spi-driver) code? Because I looked at it quickly, and it was bundled with the MacbookPro SPI Keyboard/Touchpad driver, forked from a driver that has nothing in common at all with the Touchbar functionality. I only saw later that the Touchbar-related parts are basically the same as what I pulled from the mailing list (they are the same person!). Still, what I used works well and does not pull an unneeded driver.

Moreover, the roadrunner2 repo [is not being maintained](https://github.com/roadrunner2/macbook12-spi-driver/issues/72).

Some people are [trying to merge in a touchbar driver for T2 Macs](https://www.phoronix.com/news/Apple-Touch-Bar-Linux-2024), but I am not sure if it is supposed to support T1 Macs as well or not at all (I saw no indication of T1 Macs being considered there).

### Audio

The [snd_hda_macbookpro](https://github.com/davidjo/snd_hda_macbookpro) driver [actually supports Macbook Pro 14,2](https://github.com/davidjo/snd_hda_macbookpro/issues/5), contrary to what is mentioned in <https://github.com/Dunedan/mbp-2016-linux>.

It just works if you run the scary script.

### Return from suspend

This does *not* work for me:

```
echo 0 > /sys/bus/pci/devices/0000\:01\:00.0/d3cold_allowed
```

([source](https://github.com/Dunedan/mbp-2016-linux?tab=readme-ov-file#suspend--hibernation))

It probably fixes the NVMe issue, but something else is also broken for me. Maybe some of the weird kernel modules I added is the culprit.

Neither `deep` nor even `s2idle` sleep modess let me wake the laptop up.

I don't care much about suspend at the moment, but maybe I will fix it in the future. I disable suspend in `/etc/systemd/sleep.conf`:

```
[Sleep]
AllowSuspend=no
AllowHibernation=no
AllowHybridSleep=no
AllowSuspendThenHibernate=no
```
