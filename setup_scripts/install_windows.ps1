Write-Host "Setting up your Windows environment..."

# Install Chocolatey if not already installed
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
    Write-Host "Chocolatey installed."
} else {
    Write-Host "Chocolatey is already installed."
}

# Install ngrok if not already installed
if (-not (Get-Command ngrok -ErrorAction SilentlyContinue)) {
    choco install ngrok -y
    ngrok update 
    Write-Host "ngrok installed."
} else {
    Write-Host "ngrok is already installed."
    Write-Host "ngrok is updating"
    ngrok update 
}

Write-Host "Setup complete!"
