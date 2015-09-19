How to configure launchd to run rssdler on startup on Apple's OSX.

10.5 seems to mess with the typical working of daemons, making the -d option semi-fail very loudly. This assumes you used the default install procedure (for 0.3.5 and above only, currently available only in SVN). You should set verbose = 0 and depend on log instead of the StandardOutputPath key for your logging needs:


  * create in ˜/Library/LaunchAgents/ a launchd plist file for RSSdler (rssdler.plist) with the following contents, note that you need to change /username/ to the appropriate value for the standard error path. Also, the location, /usr/bin/rssdler, may need to be changed depending on where it gets installed:
```
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC -//Apple Computer//DTD PLIST 1.0//EN http://www.apple.com/DTDs/PropertyList-1.0.dtd >
<plist version="1.0">
<dict>
  <key>Label</key>
    <string>rssdler</string>
  <key>ProgramArguments</key>
    <array>
      <string>/usr/bin/rssdler</string>
      <string>-r</string>
    </array>
  <key>StandardErrorPath</key>
    <string>/Users/username/.rssdler-error.log</string>
  <key>KeepAlive</key>
    <dict>
      <key>NetworkState</key>
        <true/>
    </dict>
</dict>
</plist>
```

  * import that file into launchd with the command: launchctl load rssdler.plist
  * Enjoy!