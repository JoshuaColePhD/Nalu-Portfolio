# Proposed Pages publishing safeguard

**Prepared for review; the repository settings have not been changed.**

Nalu currently uses legacy Pages publishing from `main:/docs`. A merge to `main`
can create a Pages deployment record even while repository Actions is disabled.
The README update remains open in [PR #3](https://github.com/JoshuaColePhD/Nalu-Portfolio/pull/3).

## Exact proposed change

After explicit approval, update only the Pages `build_type` from `legacy` to
`workflow`, using [the prepared payload](ops/pages-source-workflow.json).
Keep repository Actions disabled. Add no publishing workflow, and dispatch none.
This removes branch-based publishing as the configured source; choosing the
GitHub Actions source does not enable repository Actions.

The settings update is separate from merging this documentation PR:

```sh
gh api --method PUT repos/JoshuaColePhD/Nalu-Portfolio/pages \
  --input ops/pages-source-workflow.json
```

**Do not execute this command until the owner approves the settings change.**
Do not delete or recreate the Pages site, change its domain/HTTPS settings,
request a build, run `ship.sh`, or enable Actions.

## Baseline observed November 5, 2026

- Pages: `legacy`, source `main:/docs`, HTTPS enabled, custom domain unset.
- Repository Actions: `enabled: false`.
- Last successful Pages build: `616b743a8b8e8bdca52bd32d2383e1d895c339ee`,
  created November 3, 2026 at 21:38:31 UTC.
- Published URL: <https://joshuacolephd.github.io/Nalu-Portfolio/>.

## Verification before the README merge

1. Capture the current settings, last build, deployment records, queued/running
   Actions, and the public site's response and visible content again.
2. Apply the approved payload once. Read back `build_type: workflow` and
   `actions.enabled: false`; verify that no build or deployment has started.
3. Confirm that the existing site still serves the same content. GitHub's
   documentation defines the publishing modes but does not guarantee uninterrupted
   serving during this transition; site continuity must be checked directly.
4. If any check fails, stop and leave PR #3 unmerged. Do not automatically restore
   legacy mode, since that would reinstate the branch publishing trigger.
5. Only after the safeguard passes review and verification, retry PR #3 through
   the normal approval review. Verify again that the published build and content
   are unchanged and that no new build/deployment was created.

Restoring legacy mode or publishing a new site version requires a separate owner
instruction. This proposal performs neither action.

## GitHub references

- [Publishing sources](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [Update a Pages site](https://docs.github.com/en/rest/pages/pages#update-information-about-a-github-pages-site)
