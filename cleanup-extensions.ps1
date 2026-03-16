# VS Code Extension Cleanup Script
# Run this from a REGULAR PowerShell window (not inside VS Code)
# Usage: powershell -ExecutionPolicy Bypass -File cleanup-extensions.ps1

$extensions = @(
    # C/C++ (6)
    "ms-vscode.cpptools-extension-pack",
    "ms-vscode.cpp-devtools",
    "ms-vscode.cpptools-themes",
    "ms-vscode.cmake-tools",
    "ms-vscode.makefile-tools",
    "ms-vscode.cpptools",

    # Dart/Flutter (2)
    "dart-code.flutter",
    "dart-code.dart-code",

    # .NET (2)
    "ms-dotnettools.vscode-dotnet-modernize",
    "ms-dotnettools.vscode-dotnet-runtime",

    # Deno, Vue (2)
    "denoland.vscode-deno",
    "vue.volar",

    # Cloud/AI bloat (4)
    "googlecloudtools.cloudcode",
    "continue.continue",
    "openai.chatgpt",
    "google.geminicodeassist",

    # Unused themes (4)
    "github.github-vscode-theme",
    "enkia.tokyo-night",
    "teabyii.ayu",
    "vira.vsc-vira-theme",

    # Redundant PHP/Laravel (10)
    "devsense.phptools-vscode",
    "devsense.intelli-php-vscode",
    "devsense.composer-php-vscode",
    "devsense.profiler-php-vscode",
    "erlangparasu.goto-route-controller-laravel",
    "glitchbl.laravel-create-view",
    "ihunte.laravel-blade-wrapper",
    "naoray.laravel-goto-components",
    "pgl.laravel-jump-controller",
    "ryannaddy.laravel-artisan",

    # Java leftovers (may already be gone)
    "vscjava.vscode-java-upgrade"
)

$success = 0
$skipped = 0
$failed = 0

foreach ($ext in $extensions) {
    Write-Host "Uninstalling $ext..." -ForegroundColor Yellow
    $result = & code --uninstall-extension $ext 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  OK" -ForegroundColor Green
        $success++
    } elseif ($result -match "is not installed") {
        Write-Host "  Already removed" -ForegroundColor Gray
        $skipped++
    } else {
        Write-Host "  $result" -ForegroundColor Red
        $failed++
    }
}

Write-Host "`n=== DONE ===" -ForegroundColor Cyan
Write-Host "Uninstalled: $success  |  Already gone: $skipped  |  Failed: $failed"
Write-Host "`nRestart VS Code to apply changes."
