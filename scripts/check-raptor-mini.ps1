param (
  [Parameter(Mandatory=$false)]
  [string]$Org = "",
  [Parameter(Mandatory=$false)]
  [string]$User = ""
)

function Check-GhCli() {
  if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Error "gh CLI not found. Install GH CLI and log in (gh auth login)"
    exit 1
  }
}

Check-GhCli

if ($Org -ne "") {
  Write-Host "Checking org-level Copilot config for: $Org"
  try {
    # Try a couple of likely endpoints; the actual public API may vary depending on GitHub's version.
    $endpoints = @(
      "/orgs/$Org/settings/copilot",
      "/orgs/$Org/settings"
    )
    $found = $false
    foreach ($ep in $endpoints) {
      $resp = gh api -H "Accept: application/vnd.github+json" $ep -q || $null
      if ($resp) {
        Write-Host "Raw response for $ep:`n$resp`n"
        $found = $true
        break
      }
    }
    if (-not $found) {
      Write-Warning "Could not find a Copilot settings endpoint for org. Check UI: https://github.com/organizations/$Org/settings/copilot"
    }
  }
  catch {
    Write-Warning "Error fetching org settings: $_"
  }
}

if ($User -ne "") {
  Write-Host "Checking user-level Copilot config for: $User"
  try {
    $userResp = gh api -H "Accept: application/vnd.github+json" /users/$User -q || $null
    if ($userResp) {
      Write-Host "User API result (raw):`n$userResp`n"
      Write-Host "To check user Copilot settings, users should visit https://github.com/settings/copilot and verify experimental models and opt-in status." 
    }
    else {
      Write-Warning "No user info returned from API. Visit https://github.com/settings/copilot to check settings for $User." 
    }
  }
  catch {
    Write-Warning "Error fetching user info: $_"
  }
}

Write-Host "Done. If you need automation to set Org Copilot settings, we can craft a 'gh api' patch once we confirm the exact Org handle and required permissions."
