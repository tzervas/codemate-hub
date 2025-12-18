ENABLING RAPTOR MINI (Preview) - Organization & Personal Account Guide
=================================================================

Purpose
-------
This guide documents how to enable the GitHub Copilot experimental model "Raptor mini (Preview)" for a single GitHub organization (e.g., your Vector Weight org) and for a personal account (e.g., `tzervas`). The repo already contains a workspace setting to request the feature in `.vscode/settings.json`, but workspace settings do not override org policy. To strictly limit usage to the org + your personal account, the Copilot model must be allowed at the organization level and optionally at the user account level.

Prerequisites
-------------
- Organization owner (admin) access for the target organization
- Copilot enabled for the organization (Enterprise/Team plan or similar)
- Personal account `tzervas` with Copilot access

Example: Replace `<org>` in instructions below with your org handle (for example, `vector-weight` or `vectorweight` depending on your exact handle). If you tell me the exact org handle, I can tailor the automation snippet to use the exact name.

Organization-level enable (Admin required)
----------------------------------------
1. Sign into GitHub as an Organization owner for the org you want to restrict (example: `vector-weight` or `vectorweight`).
2. Open the organization settings page (UI path):
   - Go to: `https://github.com/organizations/<org>/settings/copilot` (replace `<org>` with your organization name).
   - If UI path unavailable: organization Settings -> Copilot -> Models (or Copilot feature toggles).
3. Find the section for models (Model selection / Model configuration / Experimental models) and enable the experimental model(s) you want — specifically "Raptor mini (Preview)".
4. Save changes. This authorizes the model for organization members and org-scoped use cases.

Personal account enable (tzervas)
--------------------------------
1. Sign into GitHub as `tzervas` (your personal account).
2. Open personal Copilot settings: `https://github.com/settings/copilot`.
3. Look for the experimental features settings and opt-in to the model(s) (Raptor mini preview) if available.

Note: After the org-level policy is enabled, workspace-level settings that request Raptor mini (see `.vscode/settings.json`) will be allowed for the org's users and your `tzervas` personal account. If a workspace-level setting is present but the model is not allowed by policy, the client will either ignore it or the Copilot extension will provide a warning.

Verify access
-------------
1. As an org member or `tzervas`, open the repo in VS Code: accept workspace settings when prompted.
2. Verify Copilot model selection: In VS Code Copilot Chat or extension settings, confirm that Raptor mini appears in the model options.
3. Optional test: run a Copilot completion or chat with the Raptor mini model and check for differences / logs.

Automating or checking via GH CLI (sample/check only)
---------------------------------------------------
There is not a simple, public REST endpoint that flips a single toggle for Copilot models without the organization admin panel or specific GraphQL/REST APIs. However, organization admins can query settings using the `gh` CLI and a token with admin scope.

Check current organization API setting (read-only check):

```bash
# Get the default org settings for the organization (must be an org admin)
gh api -H "Accept: application/vnd.github+json" /orgs/<org>/settings --jq '.copilot' || echo "no explicit Copilot settings found"
```

If you need full automation to set Copilot model policy for an org, we can draft a script for that once you confirm your org's exact name and whether you have an internal approval gate (some endpoints require Enterprise-level access). Otherwise manual UI actions are the simplest and safest approach.

Security & compliance
---------------------
- Be cautious enabling experimental or third-party models across an organization—models may use telemetry or produce different outputs. Check your organization's compliance policy and use the GitHub audit log to track changes.
- Avoid enabling experimental models for public repos unless you want them used by a wider audience.

If you want me to programmatically verify org-level Copilot configuration and optionally create a small GH CLI script to toggle the required options for `vector-weight` and `tzervas`, tell me the exact organization name and whether you have an org admin token / GH CLI admin access; I can draft a script for you.
