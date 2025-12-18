param(
  [Parameter(Mandatory=$true)]
  [string]$Org,
  [Parameter(Mandatory=$false)]
  [switch]$Apply,
  [Parameter(Mandatory=$false)]
  [string[]]$Models = @('raptor-mini','qwen2.5-coder:7b-q4_0','mistral:latest')
)

function Check-GhLoggedIn(){
  $auth = gh auth status 2>$null
  if ($LASTEXITCODE -ne 0) { Write-Error "You must be logged in with 'gh auth login' as an org admin (or run --with-token)."; exit 2 }
}

Check-GhLoggedIn

Write-Host "Checking organization Copilot settings for '$Org'..."
try {
  $resp = gh api -H "Accept: application/vnd.github+json" "/orgs/$Org/settings/copilot" -q || $null
  if (-not $resp) {
    $resp = gh api -H "Accept: application/vnd.github+json" "/orgs/$Org/settings" -q || $null
  }
  if ($resp) {
    Write-Host "Found copilot-related settings:`n$resp"
  } else {
    Write-Warning "No org copilot endpoint found, falling back to manual UI instructions."
  }
}
catch {
  Write-Warning "Unable to query org Copilot settings: $_"; $resp = $null
}

if ($Apply) {
  if ($resp -eq $null) {
    Write-Warning "Applies programmatically is not supported for this org or GH API is unavailable. Please use the UI: https://github.com/organizations/$Org/settings/copilot"
    exit 0
  }

  Write-Host "Applying Copilot settings to allow experimental models for $Org..."
  # The REST endpoint for Org Copilot settings may vary; this is a best-effort example.
  # If GitHub's public API does not support this endpoint, the command will error out and you should apply changes via the UI.
  $payload = @{
    copilot = @{
      allow_experimental_models = $true
      allowed_models = $Models
    }
  } | ConvertTo-Json -Depth 5

  try {
    gh api -X PATCH -H "Accept: application/vnd.github+json" "/orgs/$Org/settings/copilot" -F "data=$payload"
    Write-Host "Applied changes; please verify in the UI: https://github.com/organizations/$Org/settings/copilot"
  }
  catch {
    Write-Warning "Failed to apply via API - it may not be supported. Use the UI to enable these models: https://github.com/organizations/$Org/settings/copilot. Error: $_";
  }
}
else {
  Write-Host "Dry run not applying. Provide -Apply to attempt changing settings programmatically (requires org admin and working API).";
  Write-Host "Models to allow: $Models"
  Write-Host "If the endpoint doesn't exist you must enable these in the GitHub UI: https://github.com/organizations/$Org/settings/copilot"
}
