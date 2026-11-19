# Install Legesher on Windows in one line, from PowerShell:
#
#     powershell -ExecutionPolicy Bypass -c "irm https://raw.githubusercontent.com/legesher/legesher/main/install/install.ps1 | iex"
#
# -ExecutionPolicy Bypass applies to that one command only. Windows' default
# policy refuses to run script files, and this is the usual way to run an
# installer like this one without changing the policy for anything else.
#
# What it does, in order:
#   1. Finds uv (https://docs.astral.sh/uv/). When there is none, it downloads
#      the pinned uv release from GitHub, checks it against the SHA-256 below,
#      and puts uv.exe, uvx.exe and uvw.exe in %USERPROFILE%\.local\bin (or
#      $env:UV_INSTALL_DIR).
#   2. Installs the legesher CLI and the legesher-lsp language server as uv
#      tools, on Python 3.12. Every package is pinned to an exact version by the
#      constraints below; uv checks each file it downloads against the SHA-256
#      the package index publishes for it, and builds nothing from source.
#   3. Puts uv's tool folder on your user PATH with `uv tool update-shell`,
#      unless $env:LEGESHER_NO_MODIFY_PATH is 1, in which case it prints it.
#   4. Installs the VS Code extension when VS Code's `code` command is found.
#
# It never asks a question and never waits for a key press, so it runs in any
# PowerShell host. It never calls `exit`, which would close the window it was
# piped into; a failure is an error you can read. Remove what it installed with:
#
#     uv tool uninstall legesher legesher-language-server
#
# After changing a pin, run: uv run python scripts/update_installer_constraints.py

& {
    $ErrorActionPreference = 'Stop'
    Set-StrictMode -Version Latest
    # Invoke-WebRequest's progress bar slows downloads by an order of magnitude.
    $ProgressPreference = 'SilentlyContinue'

    $UvVersion = '0.13.7'
    # The oldest uv whose tool commands this relies on.
    $UvMinimum = '0.5.0'
    $ServerPython = '3.12'
    $CliPin = 'legesher==0.27.0'
    $ServerPin = 'legesher-language-server==0.3.0'
    $ExtensionId = 'legesher.legesher-vscode'
    $ManualSteps = 'https://github.com/legesher/legesher#installation'

    function Say([string] $Message) {
        Write-Host "legesher: $Message"
    }

    # Run a native program and return its exit code, with its output shown.
    # $ErrorActionPreference is Continue for the call: Windows PowerShell 5.1
    # turns each line a program writes to stderr into an error record when it
    # is redirected or when the host has no console (the ISE), and under Stop
    # the first one ends the script, though uv writes its ordinary progress
    # there.
    function Invoke-Native([string] $Program, [string[]] $Arguments) {
        $previous = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        try {
            & $Program @Arguments 2>&1 | ForEach-Object { Write-Host "$_" }
            return $LASTEXITCODE
        } finally {
            $ErrorActionPreference = $previous
        }
    }

    # Run a native program and return the last line it writes to stdout.
    function Read-Native([string] $Program, [string[]] $Arguments) {
        $previous = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        try {
            $lines = @(& $Program @Arguments 2>$null)
            if ($LASTEXITCODE -ne 0 -or $lines.Count -eq 0) { return $null }
            return ([string] $lines[-1]).Trim()
        } finally {
            $ErrorActionPreference = $previous
        }
    }

    # The SHA-256 of each uv release archive this installer may download. The
    # same values pin the VS Code extension's own install
    # (libs/vs-code/src/uvRelease.ts); scripts/tests/test_installers.py fails
    # if the two ever differ.
    # BEGIN UV CHECKSUMS
    $UvChecksums = @{
        'x86_64-pc-windows-msvc' = '0cdc5b38fe5a8168ed6a25814f5ba43c21d313dd3187314fccb37b7cec46e021'
    }
    # END UV CHECKSUMS

    $onWindows = ($PSVersionTable.PSVersion.Major -lt 6) -or $IsWindows
    if (-not $onWindows) {
        throw "legesher: this installer is for Windows; on macOS and Linux use install.sh. Install by hand: $ManualSteps"
    }
    # PROCESSOR_ARCHITEW6432 is set when a 32-bit or emulated PowerShell runs
    # on a 64-bit or ARM machine, and names the machine's own processor.
    $machine = if ($env:PROCESSOR_ARCHITEW6432) { $env:PROCESSOR_ARCHITEW6432 } else { $env:PROCESSOR_ARCHITECTURE }
    if ($machine -eq 'ARM64') {
        # lru-dict, which the language server needs, publishes no build for
        # Windows on ARM, and this installer never compiles anything.
        throw "legesher: the language server has no ready-made build for Windows on ARM. Install by hand: $ManualSteps"
    }
    if ($machine -ne 'AMD64') {
        throw "legesher: this installer does not support the $machine processor. Install by hand: $ManualSteps"
    }
    $target = 'x86_64-pc-windows-msvc'

    # Windows PowerShell 5.1 does not offer TLS 1.2 by default on older systems.
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12

    $work = Join-Path ([IO.Path]::GetTempPath()) ("legesher-" + [Guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $work -Force | Out-Null
    # uv writes UTF-8. PowerShell decodes what it reads from a program with
    # the console's code page, which would mangle a user folder named in any
    # script but ASCII. Some hosts (the ISE) refuse the change; they keep
    # their own.
    $previousEncoding = $null
    try {
        $previousEncoding = [Console]::OutputEncoding
        [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
    } catch {
        $previousEncoding = $null
    }
    try {
        $uvHome = if ($env:UV_INSTALL_DIR) { $env:UV_INSTALL_DIR } else { Join-Path $env:USERPROFILE '.local\bin' }
        $uv = $null
        $found = Get-Command uv -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($found) {
            $uv = $found.Source
        } elseif (Test-Path -LiteralPath (Join-Path $uvHome 'uv.exe')) {
            $uv = Join-Path $uvHome 'uv.exe'
        }
        if ($uv) {
            $reported = Read-Native $uv @('--version')
            $version = if ($reported) { ($reported -split ' ')[1] } else { '' }
            $parsed = $null
            if ($version -and [Version]::TryParse(($version -replace '[^0-9.].*$', ''), [ref] $parsed) -and $parsed -ge [Version] $UvMinimum) {
                Say "using the uv already installed at $uv"
            } else {
                # An older uv lacks the tool commands this needs. Leave it as
                # it is, and use the pinned uv from the temporary folder.
                Say "the uv at $uv is older than $UvMinimum; using uv $UvVersion for this install. Update yours with: uv self update"
                $uvHome = Join-Path $work 'uv-bin'
                $uv = $null
            }
        }
        if (-not $uv) {
            $url = "https://github.com/astral-sh/uv/releases/download/$UvVersion/uv-$target.zip"
            $archive = Join-Path $work "uv-$target.zip"
            Say "downloading uv $UvVersion from $url"
            Invoke-WebRequest -Uri $url -OutFile $archive -UseBasicParsing
            $expected = $UvChecksums[$target]
            $actual = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
            if ($actual -ne $expected) {
                throw "legesher: uv's download did not match its pinned checksum (expected sha256 $expected, got $actual); nothing was installed"
            }
            $unpacked = Join-Path $work 'uv'
            Expand-Archive -LiteralPath $archive -DestinationPath $unpacked -Force
            New-Item -ItemType Directory -Path $uvHome -Force | Out-Null
            foreach ($program in 'uv.exe', 'uvx.exe', 'uvw.exe') {
                Copy-Item -LiteralPath (Join-Path $unpacked $program) -Destination (Join-Path $uvHome $program) -Force
            }
            $uv = Join-Path $uvHome 'uv.exe'
            Say "installed uv $UvVersion in $uvHome"
        }

        # The exact version of every package the two tools need, for every
        # platform. Generated by scripts/update_installer_constraints.py from
        # install/requirements.in; do not edit by hand.
        $constraintsText = @'
# BEGIN CONSTRAINTS
annotated-types==0.8.0
anthropic==2.10.0
anyio==4.16.0
attrs==26.1.0
cattrs==26.2.1
certifi==2026.10.23
click==8.5.1
docstring-parser==0.18.0
h11==0.16.0
httpcore==1.0.9
httpcore2==2.16.2 ; sys_platform != 'emscripten'
httpx==0.28.1
httpx2==2.16.2
httpx2-jsfetch==1.0 ; sys_platform == 'emscripten'
idna==3.20
jinja2==3.1.6
jiter==0.19.0
jsonschema==4.26.0
jsonschema-specifications==2025.9.1
legesher==0.27.0
legesher-core==0.27.0
legesher-i18n==0.27.0
legesher-language-server==0.3.0
legesher-runtime==0.1.0
lru-dict==1.4.1
lsprotocol==2025.0.0
markdown-it-py==4.3.0
markupsafe==3.0.4
mdurl==0.1.2
ollama==0.6.3
opentelemetry-api==1.45.2
packaging==26.3
prompt-toolkit==3.0.53
pydantic==2.14.3
pydantic-core==2.50.4
pygls==2.1.1
pygments==2.21.0
pyyaml==6.0.3
questionary==2.1.1
referencing==0.37.0
rich==15.0.0
rpds-py==2026.9.1
sniffio==1.3.1
tree-sitter==0.26.1
tree-sitter-python==0.25.0
truststore==0.10.5 ; sys_platform != 'emscripten'
typing-extensions==4.16.0
typing-inspection==0.4.5
wcwidth==0.9.4
# END CONSTRAINTS
'@
        $constraints = Join-Path $work 'constraints.txt'
        # UTF-8 without a byte order mark, which uv reads as plain text.
        [IO.File]::WriteAllText($constraints, $constraintsText)

        foreach ($pin in $CliPin, $ServerPin) {
            Say "installing $pin"
            $code = Invoke-Native $uv @('tool', 'install', '--python', $ServerPython, '--no-build', '--constraints', $constraints, $pin)
            if ($code -ne 0) { throw "legesher: uv could not install $pin" }
        }

        # The folder uv puts tool commands in, as uv itself reports it.
        $toolBin = Read-Native $uv @('tool', 'dir', '--bin')
        if (-not $toolBin) { throw 'legesher: uv could not report its tool folder' }
        Say 'checking the installed commands'
        foreach ($command in 'legesher.exe', 'legesher-lsp.exe') {
            $code = Invoke-Native (Join-Path $toolBin $command) @('--version')
            if ($code -ne 0) { throw "legesher: the installed $command did not run" }
        }

        $onPath = ($env:Path -split ';') -contains $toolBin
        if (-not $onPath) {
            if ($env:LEGESHER_NO_MODIFY_PATH -eq '1') {
                Say "add this folder to your PATH to run legesher and legesher-lsp: $toolBin"
            } else {
                # uv exits non-zero when PATH already has the folder, which is
                # a success here, so its answer is not treated as a failure.
                Invoke-Native $uv @('tool', 'update-shell') | Out-Null
                # This window too, so the commands work without opening another.
                $env:Path = "$toolBin;$env:Path"
                Say "open a new terminal elsewhere to run legesher and legesher-lsp; if they are still not found, add this folder to your PATH: $toolBin"
            }
        }

        $code = Get-Command code -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($code) {
            Say 'installing the VS Code extension'
            if ((Invoke-Native $code.Source @('--install-extension', $ExtensionId)) -ne 0) {
                Say "VS Code did not install the extension; install $ExtensionId from the Extensions view"
            }
        } else {
            Say "VS Code's code command was not found; install the extension from https://marketplace.visualstudio.com/items?itemName=$ExtensionId"
        }

        Say 'done. If VS Code was open, restart it so it finds legesher-lsp.'
        Say "remove it all with: & '$uv' tool uninstall legesher legesher-language-server"
    } finally {
        if ($previousEncoding) {
            try { [Console]::OutputEncoding = $previousEncoding } catch { Write-Verbose 'could not restore the console encoding' }
        }
        Remove-Item -LiteralPath $work -Recurse -Force -ErrorAction SilentlyContinue
    }
}
