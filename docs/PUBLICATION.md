# GitHub publication

Publication status: **REPOSITORY_CREATED_RELEASE_PENDING**. The authorized public repository `erolcanustundag/freecad-mobile-lab` has been created. Source upload and the signed RC7 experimental prerelease are in progress.

The intended public repository is `freecad-mobile-lab` under the authenticated owner's account. Do not reuse an unrelated repository. Candidate releases must be marked prerelease; stable1.0 remains NOT_COMPLETE.

The GitHub integration supports file/tree/commit operations; repository creation and release upload use GitHub's signed-in interface. No credentials are stored in the public source package. The original local public-source ZIP is a sealed preparation snapshot; its publication notes predate the remote publication. Current repository notes record the actual remote state. Frozen Boost/Eigen sources are restored from that ZIP with bootstrap_vendor_sources.py; no header stubs are substituted.

Prepare and validate release assets with `scripts/package_public_release.py`. Run `python3 scripts/publish_github.py --assets dist/public-release` to check their checksums without publishing. When `gh` is authenticated to the intended owner, the explicitly authorized publication is:

```bash
python3 scripts/publish_github.py --assets dist/public-release --publish
```

It creates a new public source repository, pushes its initial source commit, creates the experimental prerelease and uploads the verified assets. It refuses an existing repository to avoid modifying unrelated work. If creation/push succeeds but a later upload fails, inspect the remote before retrying; do not blindly recreate or overwrite it.

Signing keys, private continuation files, downloaded toolchains, compiled outputs and large runtime binaries are excluded from Git. Runtime libraries belong in the prerelease asset, restored with `scripts/bootstrap_release_runtime.py`; corresponding source accompanies the binary. Keep the original private checkpoint separately when continuing development.

Verification after publishing must confirm public repository visibility, source commit/CI, prerelease status, every asset name/size/digest and actual download URLs. Do not describe publication as complete from local preparation alone.
