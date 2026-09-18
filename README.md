# RTS Data Acquisition Utilities

> **NOTICE:** _script_downloader has been replaced by a new process. See the **[Wiki](https://github.com/USACE/rts-utils/wiki)** for details._

> `rtsutils` has been refactored to act more like an installed Python package within the CAVI virtual environment. Code that once added `rtsutils` to the `PYTHONPATH`, within each script, has been removed and CAVI configurations modified by the installer placing the package in the `PYTHONPATH`. This allows for traditional `import` statements accessing `rtsutils` modules. A single `include` statement will be added to the CWMS installation CAVI configuration file (HEC-RTS.config for RTS) during the installation process.

### [Installation Instructions](https://github.com/USACE/rts-utils/wiki)


### Cumulus on CWBI

The Cumulus helper supports `cumulus.cwbi.mil` and adds the `/api` prefix to
API requests. In a watershed script, configure `Host` as `cumulus.cwbi.mil`
and `Scheme` as `https`; do not include `/api` in `Host`. Existing endpoint
strings with an `api/` prefix are also accepted. The distributed watershed
script's existing default host is unchanged; select the host for your site.

Products and watersheds are requested directly from the API. The helper no
longer probes the website root before metadata retrieval. Failed metadata
requests show the request URL and failure instead of opening an empty UI.

CWBI downloads use CAC authentication and `POST /api/downloads`. The Jython
bridge uses RTS's certificate key manager and Windows trust roots; have your
CAC inserted and complete any certificate/PIN prompt. An access token stays
in memory and is sent to the helper through stdin. It is not saved in the
watershed configuration or forwarded to other download hosts. Metadata
requests retry once with CAC authentication if the server returns HTTP 401
or 403. DNS and TLS failures are reported without initiating a login attempt.

Install the Python files together with the matching executable, then restart
RTS. The runtime changes are in:

- `rtsutils/go/windows/cavi.exe`
- `rtsutils/go/__init__.py`
- `rtsutils/go/cwbi_auth.py`
- `rtsutils/cavi/jython/ui/cumulus.py`

The integration uses Java APIs present in RTS 3.5. It does not reuse browser
cookies or implement username/password sign-in. An HTTP 403 may also indicate
network or account restrictions. If the wrong helper appears to be running,
print `go.CAVI_GO` in the RTS script editor. The helper's `-version` option
prints its build identifier without connecting to the network.

### Testing and building the Windows helper

From PowerShell in the repository root, with Go available:

```powershell
Push-Location rtsutils/go/cavi
go test -v (Get-ChildItem -Name *.go)
go build -trimpath -buildvcs=false -o ../windows/cavi.exe .
Pop-Location
```

The explicit source-file test command works around the upstream Go module's
name (`main`). The Go tests mock HTTP requests, including authenticated
downloads, metadata without a website-root probe, failed responses, and
cross-origin token protection.

Run the Jython integration tests with an RTS 3.5 installation (adjust the path):

```powershell
$rtsInstall = 'C:\APP\CWMS\HEC-RTS-3.5.0'
java -cp "$rtsInstall\shared\jar\*;$rtsInstall\shared\jar\sys\*" org.python.util.jython -B tests/test_cwbi_auth.py
```

The eight Jython tests mock token acquisition, verify cache/retry behavior and
Java exception handling, check the required RTS classes, and launch the built
helper without network access. Live CAC sign-in and downloads require a
computer with access to the CWBI services.

After changing the helper or Python package, refresh `dist/rts-utils.zip`
using the existing distribution workflow. The archive contains `rtsutils/`
at its root and is extracted into the user's `%APPDATA%\rts-utils` directory.
