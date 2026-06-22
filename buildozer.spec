[app]

title = Universal Downloader

package.name = universaldownloader

package.domain = org.vbmauro

version = 2.2.0

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,txt

requirements = python3,kivy>=2.2.0,yt-dlp,requests,certifi

android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

android.api = 33
android.minapi = 21
android.sdk = 34
android.ndk = 25b

android.archs = arm64-v8a

android.aab = 0

android.add_activity = True

android.gradle_dependencies = 'com.android.support:multidex:1.0.3'

android.extra_libs =

orientation = portrait

android.debug = 1

android.enable_apk_expansion = False

android.allow_backup = True

android.wakelock = True

p4a.fork = AndreMiras
p4a.branch = develop

[buildozer]

log_level = 2

warn_on_root = 1
