Title: Building Android main for an Xperia 10 II (Sony Open Devices supported device)
Date: 2024-08-25

I was curious how easy would it be to build AOSP for a device that I had lying around that is part of the [Sony Open Devices Program](https://developer.sony.com/open-source/aosp-on-xperia-open-devices).

The device in question is at the time of writing still supported, and was in the far-right column of the [supported devices list](https://developer.sony.com/supported-devices-and-functionality).

My device was already unlocked beforehand.

## Device

There are two devices listed under "Xperia 10 II" in the supported devices list: XQ-AU51 and XQ-AU52. That doesn't help with understanding which lunch target to use for the device I got on my hands.

The ["Resources"](https://developer.sony.com/open-source/aosp-on-xperia-open-devices/get-started/supported-devices-maintained) page helpfully linked to the right [device folder](https://github.com/sonyxperiadev/device-sony-pdx201) for these devices. There I could see that [the "aosp_xqau52" target](https://github.com/sonyxperiadev/device-sony-pdx201/blob/master/aosp_xqau52.mk) fully inherits the "aosp_xqau51" target, but setting the "dual sim" setting to true. My device has two sim card slots.

From the device.mk file in the same folder I could also see that this device inherits from the "seine" platform.

I was curious where the UART was. [There is a page for that](https://developer.sony.com/open-source/aosp-on-xperia-open-devices/guides/access-uart-ports), with a drop-down menu hidden at the very bottom of the page, stating that for this device one should somehow access the MicroSD card pins for reading from the UART.

I was lucky to have had an adapter called ["eMMC Module Reader Board for OS upgrade"](https://www.hardkernel.com/shop/emmc-module-reader-board-for-os-upgrade/) from Hardkernel, designed to let one read eMMC modules made for Odroid devices. It cost $1.50 at the time of writing. I just had to desolder the connector and solder on some PTFE wires to the correct pins. An alternative would be to get one of those "Micro SD extension cables" that I could see being sold for around $12. The PCB had to be inserted into the phone directly without using the MicroSD/SIM card tray.

Speed is 115200; standard 8-n-1.

## Sync

The device being still supported let me use the Sony [AOSP Android 14 build instruction](https://developer.sony.com/open-source/aosp-on-xperia-open-devices/guides/aosp-build-instructions/build-aosp-android-14/). I modified the repo init step, as I wanted to build main instead of 14.

(At the time of writing, the Sony instruction pointed to android-14.0.0_r50, which was not really that old. Android 14 was the latest major release.)

```
repo init --partial-clone -b main -u https://android.googlesource.com/platform/manifest
cd .repo
git clone https://github.com/sonyxperiadev/local_manifests
cd local_manifests
git checkout android-14.0.0_r50
cd ../..
repo sync -c -j8
```

\-\-partial-clone here comes from [the AOSP docs](https://source.android.com/docs/setup/download) to speed things up.

Don't try to sync with more that 8 jobs, there is a rate limit on the Google servers.

I tried to be "smart" at first and avoid using Sony's local_manifests, but it brings a lot of Qcom stuff in a convenient way, so that was not a wise attempt.

At this point I had a lot of repo sync errors. The errors were due to remove-project statements in the local_manifests that had no corresponding project (i.e. local_manifests was trying to remove projects from the to-be-synced list that were not added by the main, AOSP, manifest). I commented those remove-projects out from untracked_devices.xml, untracked_hardware.xml, and untracked_kernel.xml. Some kernel and kernel-modules prebuilts, some qcom repos, some old device folders. After this, repo sync agreed to work with me.

The next step in the instruction is:

```
./repo_update.sh
```

Looking at the suspicious script, I gathered that its function was to apply patches from [the AOSP Gerrit](https://android-review.googlesource.com/). It was applying two patches. [The first one](https://android-review.googlesource.com/q/Iad92c39fb729538cf51bf9d9037b15515104b453) was adding a definition of in_addr_t to bionic. [The second one](https://android-review.googlesource.com/q/I250006ba6fe9d91e765dde1e4534d5d87aaab879) was explicitly marked as "only for internal SODP use" and was fixing an uninitialized use of a variable in hardware/interfaces/thermal/1.0/default/Thermal.cpp. I wonder why that one is still unfixed in main.

## Build

Continuing on with the documentation:

```
source build/envsetup.sh && lunch
```

"When prompted, pick the number corresponding to your device in the list displayed and press enter."

That posed a problem right away:

```
line@DESKTOP-NNM4931:~/aosp-main$ lunch

You're building on Linux

Warning: Cannot display lunch menu.

Note: You can invoke lunch with an explicit target:

  usage: lunch [target]

Which would you like? [aosp_cf_x86_64_phone-trunk_staging-eng]
Pick from common choices above (e.g. 13) or specify your own (e.g. aosp_barbet-trunk_staging-eng):
```

The "Warning: Cannot display lunch menu." message was coming from build/make/envsetup.sh. Apparently, getting COMMON_LUNCH_CHOICES was failing. Running the failing command manually:

```
line@DESKTOP-NNM4931:~/aosp-main$ TARGET_BUILD_APPS= TARGET_PRODUCT= TARGET_RELEASE= TARGET_BUILD_VARIANT= get_build_var COMMON_LUNCH_CHOICES
In file included from build/make/core/config.mk:394:
In file included from build/make/core/envsetup.mk:55:
build/make/core/version_util.mk:167: error: Argument missing.
21:07:11 dumpvars failed with: exit status 1
line@DESKTOP-NNM4931:~/aosp-main$
```

Ok, maybe try to run lunch explicitly specifying the target?

```
line@DESKTOP-NNM4931:~/aosp-main$ lunch aosp_xqau52-userdebug

Invalid lunch combo: aosp_xqau52-userdebug
Valid combos must be of the form <product>-<release>-<variant>
line@DESKTOP-NNM4931:~/aosp-main$
```

And that is true; the [AOSP building documentation](https://source.android.com/docs/setup/build/building#choose-a-target) does mention that "release" is now part of the lunch target.

Then,
```
lunch aosp_xqau52-trunk_staging-userdebug
make
```

I had some build errors.

### Specifies both LOCAL_SDK_VERSION (system_34) and LOCAL_PRIVATE_PLATFORM_APIS (true)

```
[ 81% 91/111] including vendor/oss/timekeep/Android.mk ...
FAILED:
vendor/oss/timekeep/Android.mk: error: TimeKeep: Specifies both LOCAL_SDK_VERSION (system_34) and LOCAL_PRIVATE_PLATFORM_APIS (true) but should specify only one
In file included from build/make/core/executable.mk:79:
In file included from vendor/oss/timekeep/Android.mk:29:
In file included from build/make/core/package.mk:50:
In file included from build/make/core/package_internal.mk:377:
In file included from build/make/core/java.mk:160:
build/make/core/sdk_check.mk:34: error: done.
```

vendor/oss/timekeep/Android.mk sets LOCAL_PROPRIETARY_MODULE to true, placing the module in the vendor partition. That was done, according to git log, to make TimeKeep "compatible with Treble ROMs"

And as [one of the StackOverflow people pointed out](https://stackoverflow.com/questions/75362819/servicemode-android-mk-specifies-both-local-sdk-version-system-current-and-lo/75368434#75368434), components in vendor, product, and odm partitions [cannot use platform APIs](https://cs.android.com/android/platform/superproject/main/+/main:build/make/core/local_systemsdk.mk;l=17).

Actually reading the error message, there is [a check](https://cs.android.com/android/platform/superproject/main/+/main:build/make/core/sdk_check.mk;l=31?q=build%2Fmake%2Fcore%2Fsdk_check.mk) verifying that LOCAL_PRIVATE_PLATFORM_APIS and LOCAL_SDK_VERSION are not set simultaneously. The TimeKeep Android.mk sets LOCAL_PRIVATE_PLATFORM_APIS, wishing to use hidden APIs, but LOCAL_SDK_VERSION is not set there. It is first set [to system_current](https://cs.android.com/android/platform/superproject/main/+/main:build/make/core/local_systemsdk.mk;l=35?q=local_current_sdk.mk%20&ss=android%2Fplatform%2Fsuperproject%2Fmain) by the AOSP makefiles if a component "_cannot_use_platform_apis"; and also if so, later it is [set to system_34](https://cs.android.com/android/platform/superproject/main/+/main:build/make/core/local_current_sdk.mk;l=19) (because now "apks and jars in the vendor or odm partitions cannot use system SDK 35 and beyond"), and that's where system_34 comes from in the error message.

So, LOCAL_SDK_VERSION gets set if the module is on the wrong side of Treble. So move it back to the correct side by not setting LOCAL_PROPRIETARY_MODULE. That seems to be the only way because, per git log again, "the package depends on private APIs such as android.os.SystemProperties".

The check [appeared](https://android-review.googlesource.com/c/platform/build/+/622851) in Android P ~ Android Q times, so not sure how it should be working...

### VINTF compatibility

```
FAILED: build out/target/product/pdx201/obj/PACKAGING/check_vintf_all_intermediates/check_vintf_compatible.log
<...>
ERROR: No such file or directory: Cannot find framework matrix at FCM version 4.: No such file or directory
```

VINTF compatibility error. My favorite picture explaining how VINTF checks work is the one opening the [VINTF object overview](https://source.android.com/docs/core/architecture/vintf) page.

Here, the VINTF compatibility check is trying to compare a framework compatibility matrix and our device manifest. It complains that there is no FCM for version 4.

[Versions of FCM correspond to versions of Android](https://source.android.com/docs/core/architecture/vintf/fcm#lifecycle-codebase). Looking at the device manifest in device/sony/common/vintf/manifest.xml, it seems that its target version is version 4, which means that this device (the vendor part of Treble) implements requirements of framework (the system part of Treble) version 4 (of Android 10).

[The compatibility matrix version 4 has been removed for Android V](https://android-review.googlesource.com/c/platform/hardware/interfaces/+/2808315). "Devices with Q VINTF won't be able to update to Android V. Devices launching Q or earlier will need to update their VINTF to R or above to be able to work with Android V."

So we can try to do that by bumping target-level in device/sony/common/vintf/manifest.xml to 5.

Next error:

```
FAILED: out/target/product/pdx201/obj/PACKAGING/check_vintf_all_intermediates/check_vintf_compatible.log
ERROR: files are incompatible: The following instances are in the device manifest but not specified in framework compatibility matrix:
<...>
<a bunch of vendor.qti. and com.qualcomm.qti. APIs listed>
```

I solved this by adding a Qualcomm FCM to one of the device's product definition makefiles. Not sure why it wasn't there:

```
DEVICE_FRAMEWORK_COMPATIBILITY_MATRIX_FILE += vendor/qcom/opensource/core-utils/vendor_framework_compatibility_matrix.xml
```

Some APIs were left:

```
FAILED: out/target/product/pdx201/obj/PACKAGING/check_vintf_all_intermediates/check_vintf_compatible.log
The following instances are in the device manifest but not specified in framework compatibility matrix:
    android.hardware.configstore@1.1::ISurfaceFlingerConfigs/default
    android.hardware.light@2.0::ILight/default
    android.hardware.power@1.3::IPower/default
    android.hardware.vibrator@1.0::IVibrator/default
    vendor.nxp.nxpnfc@1.0::INxpNfc/default
    vendor.qti.hardware.radio.qtiradio@2.7::IQtiRadio/slot1
    vendor.qti.hardware.radio.qtiradio@2.7::IQtiRadio/slot2
    vendor.qti.ims.factory@2.2::IImsFactory/default
    vendor.somc.hardware.miscta@1.0::IMisctaGlobal/default
    vendor.somc.hardware.modemswitcher@1.0::IModemSwitcher/default
```

"in the device manifest but not specified in framework compatibility matrix" --- the device provides something, but the framework doesn't ask for that. I couldn't find any FCM snippets in the codebase mentioning these APIs. I didn't find anything better to do than comment those entries out from the manifests files included in the DEVICE_MANIFEST_FILE array.

### Misc errors

```
build/make/core/base_rules.mk:300: error: device/sony/common/rootdir: MODULE.TARGET.ETC.init.usb.rc already defined by system/core/rootdir.
```

Sony has a prebuilt_etc called init.usb.rc, and a different module with the same name [was added](https://android-review.googlesource.com/c/platform/system/core/+/2926193) for V. I renamed the Sony module to init.usb.sony.rc and modified the mention in PRODUCT_PACKAGES in device/sony/common/common-init.mk.

Next:

```
FAILED: target  C++: vendor.qti.hardware.display.composer-service <= vendor/qcom/opensource/display/sm8250/composer/hwc_buffer_sync_handler.cpp
Outputs: out/target/product/pdx201/obj/EXECUTABLES/vendor.qti.hardware.display.composer-service_intermediates/hwc_buffer_sync_handler.o
Error: exited with code: 1
Command: <...>
Output:
vendor/qcom/opensource/display/sm8250/composer/hwc_buffer_sync_handler.cpp:112:3: error: use of undeclared identifier 'assert'
  112 |   assert(false);
      |   ^
vendor/qcom/opensource/display/sm8250/composer/hwc_buffer_sync_handler.cpp:118:3: error: use of undeclared identifier 'assert'
  118 |   assert(false);
      |   ^
2 errors generated.
```

Someone forgot to add
```
#include <assert.h>
```
to hwc_buffer_sync_handler.cpp and I don't know how it used to compile before.

Next:

```
vendor/qcom/opensource/data-ipacfg-mgr/ipacm/inc/IPACM_Routing.h:49:17: error: using directive refers to implicitly-defined namespace 'std' [-Werror]
   49 | using namespace std;
```

I did not want to fix more questionable Qualcomm modules for the sake of a quick and minimal port, so I removed ipacm from PRODUCT_PACKAGES...

Next:

```
FAILED: target Executable: android.hardware.biometrics.fingerprint@2.1-service.sony (out/target/product/pdx201/obj/EXECUTABLES/android.hardware.biometrics.fingerprint@2.1-service.sony_intermediates/LINKED/android.hardware.biometrics.fingerprint@2.1-service.sony)
Output:
ld.lld: error: undefined hidden symbol: _ZNSt3__14swapB8ne190000IiEENS_9enable_ifIXaasr21is_move_constructibleIT_EE5valuesr18is_move_assignableIS2_EE5valueEvE4typeERS2_S5_
>>> referenced by EgisFpDevice.cpp:33 (vendor/oss/fingerprint/egistec/EgisFpDevice.cpp:33)
>>>               out/target/product/pdx201/obj/EXECUTABLES/android.hardware.biometrics.fingerprint@2.1-service.sony_intermediates/egistec/EgisFpDevice.o:(_ZN7egistec12EgisFpDeviceC2EOS0_)
clang++: error: linker command failed with exit code 1 (use -v to see invocation)
```

For the curious, `objdump -Ct out/target/product/pdx201/obj/EXECUTABLES/android.hardware.biometrics.fingerprint@2.1-service.sony_intermediates/egistec/EgisFpDevice.o` shows that this symbol demangles into `std::__1::enable_if<is_move_constructible<int>::value&&is_move_assignable<int>::value, void>::type std::__1::swap[abi:ne190000]<int>(int&, int&)`.

Initially I just removed android.hardware.biometrics.fingerprint@2.1-service.sony from PRODUCT_PACKAGES.

This meant that our device lost android.hardware.fingerprint, meaning that
```
PRODUCT_COPY_FILES += \
    frameworks/native/data/etc/android.hardware.fingerprint.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.fingerprint.xml
```
needed to be removed, otherwise the device would not boot; logs of such failure for your convenience:
```
08-11 18:37:29.991  8668  8897 W HidlToAidlSensorAdapter: NoSuchElementException
08-11 18:37:29.991  8668  8897 W HidlToAidlSensorAdapter: java.util.NoSuchElementException
08-11 18:37:29.991  8668  8897 W HidlToAidlSensorAdapter:       at android.os.HwBinder.getService(Native Method)
08-11 18:37:29.991  8668  8897 W HidlToAidlSensorAdapter:       at android.os.HwBinder.getService(HwBinder.java:93)
08-11 18:37:29.991  8668  8897 W HidlToAidlSensorAdapter:       at android.hardware.biometrics.fingerprint.V2_1.IBiometricsFingerprint.getService(IBiometricsFingerprint.java:74)
08-11 18:37:29.991  8668  8897 W HidlToAidlSensorAdapter:       at android.hardware.biometrics.fingerprint.V2_1.IBiometricsFingerprint.getService(IBiometricsFingerprint.java:84)
08-11 18:37:29.991  8668  8897 W HidlToAidlSensorAdapter:       at com.android.server.biometrics.sensors.fingerprint.hidl.HidlToAidlSensorAdapter.getIBiometricsFingerprint(HidlToAidlSensorAdapter.java:204)
08-11 18:37:29.991  8668  8897 W HidlToAidlSensorAdapter:       at com.android.server.biometrics.sensors.fingerprint.hidl.HidlToAidlSensorAdapter$$ExternalSyntheticLambda6.get(R8$$SyntheticClass:0)
08-11 18:37:29.991  8668  8897 W HidlToAidlSensorAdapter:       at com.android.server.biometrics.sensors.fingerprint.hidl.HidlToAidlSessionAdapter.setActiveGroup(HidlToAidlSessionAdapter.java:217)
08-11 18:37:29.991  8668  8897 W HidlToAidlSensorAdapter:       at com.android.server.biometrics.sensors.fingerprint.hidl.FingerprintUpdateActiveUserClient.startHalOperation(FingerprintUpdateActiveUserClient.java:124)
08-11 18:37:29.991  8668  8897 W HidlToAidlSensorAdapter:       at com.android.server.biometrics.sensors.fingerprint.hidl.FingerprintUpdateActiveUserClient.start(FingerprintUpdateActiveUserClient.java:110)
08-11 18:37:29.991  8668  8897 W HidlToAidlSensorAdapter:       at com.android.server.biometrics.sensors.BiometricScheduler.startNextOperation(BiometricScheduler.java:339)
08-11 18:37:29.991  8668  8897 W HidlToAidlSensorAdapter:       at com.android.server.biometrics.sensors.BiometricScheduler.startNextOperationIfIdle(BiometricScheduler.java:309)
08-11 18:37:29.991  8668  8897 W HidlToAidlSensorAdapter:       at com.android.server.biometrics.sensors.BiometricScheduler.scheduleClientMonitor(BiometricScheduler.java:507)
08-11 18:37:29.991  8668  8897 W HidlToAidlSensorAdapter:       at com.android.server.biometrics.sensors.fingerprint.aidl.FingerprintProvider.scheduleForSensor(FingerprintProvider.java:416)
08-11 18:37:29.991  8668  8897 W HidlToAidlSensorAdapter:       at com.android.server.biometrics.sensors.fingerprint.aidl.FingerprintProvider.lambda$scheduleInternalCleanup$15(FingerprintProvider.java:754)
08-11 18:37:29.991  8668  8897 W HidlToAidlSensorAdapter:       at com.android.server.biometrics.sensors.fingerprint.aidl.FingerprintProvider.$r8$lambda$SHdzB0Q0nTaCyLOEaZChAtjwo9c(FingerprintProvider.java:0)
08-11 18:37:29.991  8668  8897 W HidlToAidlSensorAdapter:       at com.android.server.biometrics.sensors.fingerprint.aidl.FingerprintProvider$$ExternalSyntheticLambda0.run(R8$$SyntheticClass:0)
08-11 18:37:29.991  8668  8897 W HidlToAidlSensorAdapter:       at android.os.Handler.handleCallback(Handler.java:959)
08-11 18:37:29.991  8668  8897 W HidlToAidlSensorAdapter:       at android.os.Handler.dispatchMessage(Handler.java:100)
08-11 18:37:29.991  8668  8897 W HidlToAidlSensorAdapter:       at android.os.Looper.loopOnce(Looper.java:232)
08-11 18:37:29.991  8668  8897 W HidlToAidlSensorAdapter:       at android.os.Looper.loop(Looper.java:317)
08-11 18:37:29.991  8668  8897 W HidlToAidlSensorAdapter:       at android.os.HandlerThread.run(HandlerThread.java:85)
08-11 18:37:29.993  8668  8897 W HidlToAidlSensorAdapter: Fingerprint HAL not available
08-11 18:37:29.993  8668  8668 V SystemServerTiming: StartShortcutServiceLifecycle took to complete: 8ms
08-11 18:37:29.994  8668  8668 D SystemServerTiming: StartLauncherAppsService
08-11 18:37:29.994  8668  8668 I SystemServiceManager: Starting com.android.server.pm.LauncherAppsService
08-11 18:37:29.995  8668  8897 E AndroidRuntime: *** FATAL EXCEPTION IN SYSTEM PROCESS: FingerprintHandler
08-11 18:37:29.995  8668  8897 E AndroidRuntime: java.lang.NullPointerException: Attempt to invoke interface method 'int android.hardware.biometrics.fingerprint.V2_1.IBiometricsFingerprint.setActiveGroup(int, java.lang.String)' on a null object reference
08-11 18:37:29.995  8668  8897 E AndroidRuntime:        at com.android.server.biometrics.sensors.fingerprint.hidl.HidlToAidlSessionAdapter.setActiveGroup(HidlToAidlSessionAdapter.java:217)
08-11 18:37:29.995  8668  8897 E AndroidRuntime:        at com.android.server.biometrics.sensors.fingerprint.hidl.FingerprintUpdateActiveUserClient.startHalOperation(FingerprintUpdateActiveUserClient.java:124)
08-11 18:37:29.995  8668  8897 E AndroidRuntime:        at com.android.server.biometrics.sensors.fingerprint.hidl.FingerprintUpdateActiveUserClient.start(FingerprintUpdateActiveUserClient.java:110)
08-11 18:37:29.995  8668  8897 E AndroidRuntime:        at com.android.server.biometrics.sensors.BiometricScheduler.startNextOperation(BiometricScheduler.java:339)
08-11 18:37:29.995  8668  8897 E AndroidRuntime:        at com.android.server.biometrics.sensors.BiometricScheduler.startNextOperationIfIdle(BiometricScheduler.java:309)
08-11 18:37:29.995  8668  8897 E AndroidRuntime:        at com.android.server.biometrics.sensors.BiometricScheduler.scheduleClientMonitor(BiometricScheduler.java:507)
08-11 18:37:29.995  8668  8897 E AndroidRuntime:        at com.android.server.biometrics.sensors.fingerprint.aidl.FingerprintProvider.scheduleForSensor(FingerprintProvider.java:416)
08-11 18:37:29.995  8668  8897 E AndroidRuntime:        at com.android.server.biometrics.sensors.fingerprint.aidl.FingerprintProvider.lambda$scheduleInternalCleanup$15(FingerprintProvider.java:754)
08-11 18:37:29.995  8668  8897 E AndroidRuntime:        at com.android.server.biometrics.sensors.fingerprint.aidl.FingerprintProvider.$r8$lambda$SHdzB0Q0nTaCyLOEaZChAtjwo9c(FingerprintProvider.java:0)
08-11 18:37:29.995  8668  8897 E AndroidRuntime:        at com.android.server.biometrics.sensors.fingerprint.aidl.FingerprintProvider$$ExternalSyntheticLambda0.run(R8$$SyntheticClass:0)
08-11 18:37:29.995  8668  8897 E AndroidRuntime:        at android.os.Handler.handleCallback(Handler.java:959)
08-11 18:37:29.995  8668  8897 E AndroidRuntime:        at android.os.Handler.dispatchMessage(Handler.java:100)
08-11 18:37:29.995  8668  8897 E AndroidRuntime:        at android.os.Looper.loopOnce(Looper.java:232)
08-11 18:37:29.995  8668  8897 E AndroidRuntime:        at android.os.Looper.loop(Looper.java:317)
08-11 18:37:29.995  8668  8897 E AndroidRuntime:        at android.os.HandlerThread.run(HandlerThread.java:85)
08-11 18:37:29.997   517  8905 W libc    : Unable to set property "ctl.interface_start" to "android.hardware.biometrics.fingerprint@2.1::IBiometricsFingerprint/default": PROP_ERROR_HANDLE_CONTROL_MESSAGE (0x20)
08-11 18:37:29.999   517  8905 I hwservicemanager: Tried to start android.hardware.biometrics.fingerprint@2.1::IBiometricsFingerprint/default as a lazy service, but was unable to. Usually this happens when a service is not installed, but if the service is intended to be used as a lazy service, then it may be configured incorrectly.
08-11 18:37:30.001  8668  8668 V SystemServerTiming: StartLauncherAppsService took to complete: 7ms
08-11 18:37:30.001  8668  8668 D SystemServerTiming: StartCrossProfileAppsService
08-11 18:37:30.002  8668  8668 I SystemServiceManager: Starting com.android.server.pm.CrossProfileAppsService
08-11 18:37:30.004  8668  8668 V SystemServerTiming: StartCrossProfileAppsService took to complete: 2ms
08-11 18:37:30.004  8668  8668 D SystemServerTiming: StartPeopleService
08-11 18:37:30.004  8668  8668 I SystemServiceManager: Starting com.android.server.people.PeopleService
08-11 18:37:30.008  8668  8897 I DropBoxManagerService: add tag=system_server_crash isTagEnabled=true flags=0x2
08-11 18:37:29.984     0     0 E init    : Control message: Could not find 'android.hardware.biometrics.fingerprint@2.1::IBiometricsFingerprint/default' for ctl.interface_start from pid: 517 (/system/system_ext/bin/hwservicemanager)
08-11 18:37:30.003     0     0 E init    : Control message: Could not find 'android.hardware.biometrics.fingerprint@2.1::IBiometricsFingerprint/default' for ctl.interface_start from pid: 517 (/system/system_ext/bin/hwservicemanager)
08-11 18:37:30.015  8668  8668 V SystemServerTiming: StartPeopleService took to complete: 11ms
08-11 18:37:30.015  8668  8668 D SystemServerTiming: StartMediaMetricsManager
08-11 18:37:30.016  8668  8668 I SystemServiceManager: Starting com.android.server.media.metrics.MediaMetricsManagerService
08-11 18:37:30.016   517  8907 W libc    : Unable to set property "ctl.interface_start" to "android.hardware.biometrics.fingerprint@2.1::IBiometricsFingerprint/default": PROP_ERROR_HANDLE_CONTROL_MESSAGE (0x20)
08-11 18:37:30.017   517  8907 I hwservicemanager: Tried to start android.hardware.biometrics.fingerprint@2.1::IBiometricsFingerprint/default as a lazy service, but was unable to. Usually this happens when a service is not installed, but if the service is intended to be used as a lazy service, then it may be configured incorrectly.
08-11 18:37:30.020  8668  8668 V SystemServerTiming: StartMediaMetricsManager took to complete: 5ms
08-11 18:37:30.020  8668  8668 D SystemServerTiming: StartBackgroundInstallControlService
08-11 18:37:30.021  8668  8668 I SystemServiceManager: Starting com.android.server.pm.BackgroundInstallControlService
08-11 18:37:30.026  8668  8668 V SystemServerTiming: StartBackgroundInstallControlService took to complete: 5ms
08-11 18:37:30.027  8668  8668 D SystemServerTiming: StartMediaProjectionManager
08-11 18:37:30.027  8668  8668 I SystemServiceManager: Starting com.android.server.media.projection.MediaProjectionManagerService
08-11 18:37:30.031  8668  8897 I Process : Sending signal. PID: 8668 SIG: 9
08-11 18:37:30.083  8459  8459 D nativeloader: Load libframework-connectivity-jni.so using APEX ns com_android_tethering for caller /apex/com.android.tethering/javalib/framework-connectivity.jar: ok
08-11 18:37:30.170   514   514 I lowmemorykiller: lmkd data connection dropped
08-11 18:37:30.171   514   514 I lowmemorykiller: closing lmkd data connection
08-11 18:37:30.174  8463  8499 E CameraService: UidPolicy: Failed to remove uid from observer: 0xffffffe0
08-11 18:37:30.174  8462  8462 I CaptureStateNotifier: Listener binder died
08-11 18:37:30.174  8464  8464 E ResourceManagerMetrics: UidObserver: ActivityManager has died
08-11 18:37:30.182     0     0 I binder  : 8463:8499 transaction failed 29189/-22, size 140-8 line 3103
08-11 18:37:30.180  8461  8461 E Zygote  : Zygote failed to write to system_server FD: Connection refused
08-11 18:37:30.180  8461  8461 I Zygote  : Process 8668 exited due to signal 9 (Killed)
08-11 18:37:30.180  8461  8461 E Zygote  : Exit zygote because system server (pid 8668) has terminated
```

But spending a bit more time on this error later on, I discovered that this error message plainly means "vendor/oss/fingerprint/egistec/EgisFpDevice.cpp does not include `<utility>`". Adding `<utility>` fixes this error.

This error is specific to LLVM's libc++. There is an inclusion chain happening, where vendor/oss/fingerprint/FormatException.hpp includes `<exception>`, and that eventually pulls in is_swappable.h; and is_swappable declares std::swap the way it is declared in the linker error. Including `<utility>` pulls in an implementation of std::swap with swap.h. I [complained](https://github.com/llvm/llvm-project/issues/106007) about this error message unclarity on LLVM's issue tracker; seemed to be a known issue.

## Flashing

For this device:

* Power + VolUp goes to Fastboot (blue LED)
* Power + VolDn goes to the rescue (Emma) mode (green LED)
* Holding all three buttons resets the device

Flashing is covered [in the Sony's guide](https://developer.sony.com/open-source/aosp-on-xperia-open-devices/guides/aosp-build-instructions/build-aosp-android-14/) as well.

```
fastboot flash boot boot.img
fastboot flash recovery recovery.img
fastboot flash dtbo dtbo.img
fastboot flash vbmeta vbmeta.img --disable-verity --disable-verification
fastboot flash oem SW_binaries_for_Xperia_Android_13_4.19_v4a_seine.img
# reboot into fastbootd
fastboot reboot fastboot
fastboot flash vendor vendor.img
fastboot flash system system.img
fastboot flash vbmeta_system vbmeta_system.img --disable-verity --disable-verification
fastboot flash product product.img
fastboot flash userdata userdata.img
fastboot erase metadata
```

## No serial

Sony Open Devices has a [separate repository serving as a bug tracker](https://github.com/sonyxperiadev/bug_tracker).

When I flashed the device, I had no logs from the kernel, the last line of the bootloader stating:
```
EFI_UdonStop Stop DebugPort for anti-corroding
```

I [sent this question to the tracker](https://github.com/sonyxperiadev/bug_tracker/issues/842), and got an answer very quick:

```
BOARD_KERNEL_CMDLINE += earlycon=msm_geni_serial,0x4a90000
BOARD_KERNEL_CMDLINE += console=ttyMSM0,115200,n8 androidboot.console=ttyMSM0
```
need to be added to BoardConfig (they can be found commented out in device/sony/common/CommonConfig.mk and device/sony/seine/PlatformConfig.mk), and

```
CONFIG_SERIAL_MSM_GENI_CONSOLE=y
```

needs to be added to `kernel/sony/msm-4.19/kernel/arch/arm64/configs/aosp_seine_pdx201_defconfig`.

To rebuild the kernel, there is a [page](https://developer.sony.com/open-source/aosp-on-xperia-open-devices/guides/kernel-compilation-guides/how-to-build-and-flash-a-linux-kernel-for-aosp-supported-devices/how-to-autimatically-build-the-linux-kernel/) on Sony's website, but I had to stray from that instruction to actually get the kernel rebuilt with my new config:

```
rm -r device/sony/common-kernel
cd kernel/sony/msm-4.19/common-kernel
./build-kernels-clang.sh
m bootimage
```

I also modified the value of PLATFORMS in kernel/sony/msm-4.19/common-kernel/build_shared_vars.sh to make sure the script only builds the kernel for seine.


## bpffs labeling

The device wouldn't boot. It was stuck on the Android logo, SystemUI not starting. Luckily, ADB was appearing a couple of minutes into the boot (quite unstable at first, but stable later on).

```
08-11 18:34:25.347  6356  6356 E jniClatCoordinator: context of '/sys/fs/bpf/net_shared' is 'u:object_r:fs_bpf:s0' != 'u:object_r:fs_bpf_net_shared:s0'
08-11 18:34:25.347  6356  6356 E jniClatCoordinator: context of '/sys/fs/bpf/net_shared/prog_clatd_schedcls_egress4_clat_rawip' is 'u:object_r:fs_bpf:s0' != 'u:object_r:fs_bpf_net_shared:s0'
08-11 18:34:25.347  6356  6356 E jniClatCoordinator: context of '/sys/fs/bpf/net_shared/prog_clatd_schedcls_ingress6_clat_rawip' is 'u:object_r:fs_bpf:s0' != 'u:object_r:fs_bpf_net_shared:s0'
08-11 18:34:25.348  6356  6356 E jniClatCoordinator: context of '/sys/fs/bpf/net_shared/prog_clatd_schedcls_ingress6_clat_ether' is 'u:object_r:fs_bpf:s0' != 'u:object_r:fs_bpf_net_shared:s0'
08-11 18:34:25.348  6356  6356 E jniClatCoordinator: context of '/sys/fs/bpf/net_shared/map_clatd_clat_egress4_map' is 'u:object_r:fs_bpf:s0' != 'u:object_r:fs_bpf_net_shared:s0'
08-11 18:34:25.348  6356  6356 E jniClatCoordinator: context of '/sys/fs/bpf/net_shared/map_clatd_clat_ingress6_map' is 'u:object_r:fs_bpf:s0' != 'u:object_r:fs_bpf_net_shared:s0'
08-11 18:34:25.349  6356  6356 F libc    : Fatal signal 6 (SIGABRT), code -1 (SI_QUEUE) in tid 6356 (system_server), pid 6356 (system_server)
<...>
08-11 18:34:26.000  6527  6527 F DEBUG   : Build fingerprint: 'Sony/aosp_xqau52/pdx201:VanillaIceCream/MAIN/eng.line.00000000.000000:userdebug/test-keys'
08-11 18:34:26.000  6527  6527 F DEBUG   : Revision: '0'
08-11 18:34:26.000  6527  6527 F DEBUG   : ABI: 'arm64'
08-11 18:34:26.000  6527  6527 F DEBUG   : Timestamp: 2024-08-11 18:34:25.546763705+0000
08-11 18:34:26.001  6527  6527 F DEBUG   : Process uptime: 8s
08-11 18:34:26.001  6527  6527 F DEBUG   : Cmdline: system_server
08-11 18:34:26.001  6527  6527 F DEBUG   : pid: 6356, tid: 6356, name: system_server  >>> system_server <<<
08-11 18:34:26.001  6527  6527 F DEBUG   : uid: 1000
08-11 18:34:26.002  6527  6527 F DEBUG   : signal 6 (SIGABRT), code -1 (SI_QUEUE), fault addr --------
08-11 18:34:26.002  6527  6527 F DEBUG   :     x0  0000000000000000  x1  00000000000018d4  x2  0000000000000006  x3  0000007fd943d7e0
08-11 18:34:26.002  6527  6527 F DEBUG   :     x4  716067725e73646d  x5  716067725e73646d  x6  716067725e73646d  x7  7f7f7f7f7f7f7f7f
08-11 18:34:26.002  6527  6527 F DEBUG   :     x8  00000000000000f0  x9  0e63736706bdf53a  x10 000000ff00000020  x11 fffffffffffffffd
08-11 18:34:26.003  6527  6527 F DEBUG   :     x12 0000007fd943bed0  x13 000000000000007f  x14 0000007fd943d1b8  x15 0000000000000000
08-11 18:34:26.003  6527  6527 F DEBUG   :     x16 00000073e5932040  x17 00000073e591d630  x18 00000073fe8e0000  x19 00000000000018d4
08-11 18:34:26.003  6527  6527 F DEBUG   :     x20 00000000000018d4  x21 00000000ffffffff  x22 00000073fdbb6a80  x23 000000703ea38078
08-11 18:34:26.003  6527  6527 F DEBUG   :     x24 b400007315eeb610  x25 0000007fd943da79  x26 b400007155f13780  x27 b400007315eeb610
08-11 18:34:26.004  6527  6527 F DEBUG   :     x28 00000073fdb96025  x29 0000007fd943d860
08-11 18:34:26.004  6527  6527 F DEBUG   :     lr  00000073e58bc4f0  sp  0000007fd943d7e0  pc  00000073e58bc514  pst 0000000000000000
08-11 18:34:26.004  6527  6527 F DEBUG   : 48 total frames
08-11 18:34:26.004  6527  6527 F DEBUG   : backtrace:
<...>
```

The backtrace processed with `stack`:
```
Stack Trace:
  RELADDR           FUNCTION                                                               FILE:LINE
  000000000005b514  abort+156                                                              bionic/libc/bionic/abort.cpp:52
  v-------------->  android::verifyClatPerms()                                             packages/modules/Connectivity/service/jni/com_android_server_connectivity_ClatCoordinator.cpp:135
  0000000000007d18  android::register_com_android_server_connectivity_ClatCoordinator+712  packages/modules/Connectivity/service/jni/com_android_server_connectivity_ClatCoordinator.cpp:565
  000000000000b120  JNI_OnLoad+168                                                         packages/modules/Connectivity/service/jni/onload.cpp:46
  00000000004a5038  art::JavaVMExt::LoadNativeLibrary+1660                                 art/runtime/jni/java_vm_ext.cc:1117
  0000000000005638  JVM_NativeLoad+376                                                     art/openjdkjvm/OpenjdkJvm.cc:362
  0000000000311700  art_quick_generic_jni_trampoline+144                                   art/runtime/arch/arm64/quick_entrypoints_arm64.S:1828
  000000000075f488  NterpCommonInvokeStatic+120                                            out/soong/.intermediates/art/runtime/libart_mterp.arm64ng/gen/mterp_arm64ng.S:11403
  000000000010aaf0  java.lang.Runtime.loadLibrary0+92                                      /apex/com.android.art/javalib/core-oj.jar
  0000000000760344  NterpCommonInvokeInstance+20                                           out/soong/.intermediates/art/runtime/libart_mterp.arm64ng/gen/mterp_arm64ng.S:11409
  000000000010aa7c  java.lang.Runtime.loadLibrary0+8                                       /apex/com.android.art/javalib/core-oj.jar
  0000000000760344  NterpCommonInvokeInstance+20                                           out/soong/.intermediates/art/runtime/libart_mterp.arm64ng/gen/mterp_arm64ng.S:11409
  0000000000116130  java.lang.System.loadLibrary+16                                        /apex/com.android.art/javalib/core-oj.jar
  000000000075f424  NterpCommonInvokeStatic+20                                             out/soong/.intermediates/art/runtime/libart_mterp.arm64ng/gen/mterp_arm64ng.S:11403
  00000000000e492a  com.android.server.NetworkStatsServiceInitializer.<init>+10            /apex/com.android.tethering/javalib/service-connectivity.jar
  00000000002fa394  art_quick_invoke_stub+612                                              art/runtime/arch/arm64/quick_entrypoints_arm64.S:699
  00000000002b445c  art::ArtMethod::Invoke+132                                             art/runtime/art_method.cc:421
  v-------------->  art::::InvokeWithArgArray                                              art/runtime/reflection.cc:458
  v-------------->  art::::InvokeMethodImpl                                                art/runtime/reflection.cc:493
  00000000002b9fec  art::InvokeConstructor+368                                             art/runtime/reflection.cc:832
  00000000006dcf20  art::Constructor_newInstance0 +320                                     art/runtime/native/java_lang_reflect_Constructor.cc:118
  0000000000311700  art_quick_generic_jni_trampoline+144                                   art/runtime/arch/arm64/quick_entrypoints_arm64.S:1828
  00000000007603a0  NterpCommonInvokeInstance+112                                          out/soong/.intermediates/art/runtime/libart_mterp.arm64ng/gen/mterp_arm64ng.S:11409
  000000000012da74  java.lang.reflect.Constructor.newInstance+8                            /apex/com.android.art/javalib/core-oj.jar
  0000000000760344  NterpCommonInvokeInstance+20                                           out/soong/.intermediates/art/runtime/libart_mterp.arm64ng/gen/mterp_arm64ng.S:11409
  0000000000237a3e  com.android.server.SystemServiceManager.startService+158               /system/framework/services.jar
  0000000000760344  NterpCommonInvokeInstance+20                                           out/soong/.intermediates/art/runtime/libart_mterp.arm64ng/gen/mterp_arm64ng.S:11409
  0000000000237c1c  com.android.server.SystemServiceManager.startServiceFromJar+36         /system/framework/services.jar
  0000000000760344  NterpCommonInvokeInstance+20                                           out/soong/.intermediates/art/runtime/libart_mterp.arm64ng/gen/mterp_arm64ng.S:11409
  00000000002355c4  com.android.server.SystemServer.startOtherServices+3640                /system/framework/services.jar
  0000000000760344  NterpCommonInvokeInstance+20                                           out/soong/.intermediates/art/runtime/libart_mterp.arm64ng/gen/mterp_arm64ng.S:11409
  0000000000233ae4  com.android.server.SystemServer.run+792                                /system/framework/services.jar
  0000000000760344  NterpCommonInvokeInstance+20                                           out/soong/.intermediates/art/runtime/libart_mterp.arm64ng/gen/mterp_arm64ng.S:11409
  0000000000233636  com.android.server.SystemServer.main+10                                /system/framework/services.jar
  00000000002fa660  art_quick_invoke_static_stub+640                                       art/runtime/arch/arm64/quick_entrypoints_arm64.S:718
  00000000002b44a4  art::ArtMethod::Invoke+204                                             art/runtime/art_method.cc:423
  v-------------->  art::::InvokeWithArgArray                                              art/runtime/reflection.cc:458
  v-------------->  art::::InvokeMethodImpl                                                art/runtime/reflection.cc:493
  00000000002b8b60  _jobject* art::InvokeMethod<(art::PointerSize)8>+444                   art/runtime/reflection.cc:773
  0000000000684c54  art::Method_invoke +32                                                 art/runtime/native/java_lang_reflect_Method.cc:86
  0000000000311700  art_quick_generic_jni_trampoline+144                                   art/runtime/arch/arm64/quick_entrypoints_arm64.S:1828
  00000000007603a0  NterpCommonInvokeInstance+112                                          out/soong/.intermediates/art/runtime/libart_mterp.arm64ng/gen/mterp_arm64ng.S:11409
  00000000005355f2  com.android.internal.os.RuntimeInit$MethodAndArgsCaller.run+18         /system/framework/framework.jar
  0000000000761164  NterpCommonInvokeInterface+20                                          out/soong/.intermediates/art/runtime/libart_mterp.arm64ng/gen/mterp_arm64ng.S:11415
  0000000000539d82  com.android.internal.os.ZygoteInit.main+558                            /system/framework/framework.jar
  00000000002fa660  art_quick_invoke_static_stub+640                                       art/runtime/arch/arm64/quick_entrypoints_arm64.S:718
  00000000002b44a4  art::ArtMethod::Invoke+204                                             art/runtime/art_method.cc:423
  v-------------->  art::::InvokeWithArgArray                                              art/runtime/reflection.cc:458
  v-------------->  art::JValue art::InvokeWithVarArgs<art::ArtMethod*>                    art/runtime/reflection.cc:551
  00000000002b4844  art::JValue art::InvokeWithVarArgs<_jmethodID*>+620                    art/runtime/reflection.cc:566
  000000000072a420  art::JNI<true>::CallStaticVoidMethodV+156                              art/runtime/jni/jni_internal.cc:1966
  00000000000d2fcc  _JNIEnv::CallStaticVoidMethod+104                                      libnativehelper/include_jni/jni.h:779
  00000000000de8cc  android::AndroidRuntime::start+848                                     frameworks/base/core/jni/AndroidRuntime.cpp:1299
  0000000000002564  main+1200                                                              frameworks/base/cmds/app_process/app_main.cpp:0
  000000000005514c  __libc_init+116                                                        bionic/libc/bionic/libc_init_dynamic.cpp:170
```

The error message tells enough: this ClatCoordinator checks that /sys/fs/bpf/net_shared is labeled correctly, which was not the case:
```
pdx201:/ $ ls -lZ /sys/fs/bpf/net_shared
total 0
-rw-rw---- 1 root system u:object_r:fs_bpf:s0  0 1973-04-13 01:30 map_block_blocked_ports_map
-rw-rw---- 1 root system u:object_r:fs_bpf:s0  0 1973-04-13 01:30 map_clatd_clat_egress4_map
-rw-rw---- 1 root system u:object_r:fs_bpf:s0  0 1973-04-13 01:30 map_clatd_clat_ingress6_map
-rw-rw---- 1 root system u:object_r:fs_bpf:s0  0 1973-04-13 01:30 map_dscpPolicy_ipv4_dscp_policies_map
-rw-rw---- 1 root system u:object_r:fs_bpf:s0  0 1973-04-13 01:30 map_dscpPolicy_ipv6_dscp_policies_map
-rw-rw---- 1 root system u:object_r:fs_bpf:s0  0 1973-04-13 01:30 map_dscpPolicy_socket_policy_cache_map
-r--r----- 1 root system u:object_r:fs_bpf:s0  0 1973-04-13 01:30 prog_clatd_schedcls_egress4_clat_rawip
-r--r----- 1 root system u:object_r:fs_bpf:s0  0 1973-04-13 01:30 prog_clatd_schedcls_ingress6_clat_ether
-r--r----- 1 root system u:object_r:fs_bpf:s0  0 1973-04-13 01:30 prog_clatd_schedcls_ingress6_clat_rawip
pdx201:/ $ ls -ldZ /sys/fs/bpf/net_shared
drwxrwxrwt 2 root root u:object_r:fs_bpf:s0  0 1973-04-13 01:30 /sys/fs/bpf/net_shared
pdx201:/ $
```

This took me a while to figure out. system/sepolicy/private/genfs_contexts was clearly stating that net_shared has to be labeled with fs_bpf_net_shared. When I began suspecting the kernel, I found that I was missing [a patch that allowed genfscon to actually set labels to bpf files](https://lore.kernel.org/all/20200206165527.211350-1-smoreland@google.com/).

How was my kernel missing a patch? I checked [the AOSP-kernel compatibility matrix](https://source.android.com/docs/core/architecture/kernel/android-common#compatibility-matrix). Android 15 was marked as compatible with android-4.19-stable. But what kernel does Sony have? pdx201 is using msm-4.19, so _some_ 4.19. This kernel's top-level Makefile claimed it was a 4.19.248.

I added [the Common Android Kernel](https://android.googlesource.com/kernel/common) as a second remote to kernel/sony/msm-4.19/kernel and found that this patch was merged into android-4.19-stable on 2021-11-06.

I also found that the Sony kernel does not share its history with the Android kernel history at all; it branches out from the Torvalds' tree. And the Torvalds' tree only got this change for 5.6.0.

The Sony kernel's history has a bunch of changes from 2022-08-25, each of them having a commit message like "treewide: 4.19.219", from "treewide: 4.19.189" to "treewide: 4.19.248", to be exact. And the change for 4.19.216 is missing this patch.

This brought me to the conclusion that the kernel Sony is using for this device is not an Android kernel at all. It is the Torvalds' mainline kernel with some patches carried over.

Anyway, I cherry-picked this patch, rebuilt the kernel, reflashed the device, and got:
```
[sys.boot_completed]: [1]
```

Not awful performance-wise. Camera works. Bluetooth works. A lot of other things don't work, and don't look into the logcat.
