# GitHub publication

Current full release: **1.4/code30**, https://github.com/erolcanustundag/freecad-mobile-lab/releases/tag/v1.4 . Non-draft, non-prerelease and latest; four assets and exact source/tag independently verified. Publication workflow38430079995 and sourceCI38428928909 passed; its temporary transport branch was deleted. Physical Android1.4 execution and full workbench parity remain pending. Earlier publication records below are historical.


Product1.0 publication status: **PUBLISHED_FULL_FEATURE_RELEASE**. Signed1.0 release: https://github.com/erolcanustundag/freecad-mobile-lab/releases/tag/v1.0 . It is non-draft, non-prerelease and latest; all four asset sizes/SHA256 digests match. Source CI and release workflow passed; the temporary transport branch was removed. The already verified RC7 publication remains **PUBLISHED_EXPERIMENTAL_PRERELEASE**. Public repository: https://github.com/erolcanustundag/freecad-mobile-lab . Signed RC7 prerelease: https://github.com/erolcanustundag/freecad-mobile-lab/releases/tag/v1.0-rc7 . All four original asset sizes/SHA256 values match GitHub’s recorded digests. Source checks and the release workflow passed; the temporary transport branch was removed. Android runtime and full FreeCAD parity remain incomplete.

The intended public repository is `freecad-mobile-lab` under the authenticated owner's account. Do not reuse an unrelated repository. Candidate releases must be marked prerelease. Product1.0 is a full release of the current mobile feature set; the earlier complete-FreeCAD-parity/qualification milestone remains NOT_COMPLETE. Its manifest explicitly sets prerelease=false.

The GitHub integration published the source. Repository creation used the signed-in interface; a credential-session restriction then blocked browser asset uploads. A temporary GitHub workflow reassembled and verified public artifact bytes, uploaded the unchanged signed APK/bundles, published the prerelease and removed its transport branch. Signing keys were not inputs to that workflow. No credentials are stored in the public source package. Each public-source ZIP is a sealed preparation snapshot; its publication notes predate its remote publication. Current repository notes record the actual remote state. Frozen Boost/Eigen sources are restored from that ZIP with bootstrap_vendor_sources.py; no header stubs are substituted.

Prepare and validate release assets with `scripts/package_public_release.py`. Run `python3 scripts/publish_github.py --assets dist/public-release` to check their checksums without publishing. When `gh` is authenticated to the intended owner, the explicitly authorized publication is:

```bash
python3 scripts/publish_github.py --assets dist/public-release --publish
```

The CLI helper is for initial repository creation: it creates a new public source repository, pushes its initial source commit and uploads the verified assets with the manifest release channel. Existing-repository updates use a reviewed fast-forward source commit and a separately verified release workflow. It refuses an existing repository to avoid modifying unrelated work. If creation/push succeeds but a later upload fails, inspect the remote before retrying; do not blindly recreate or overwrite it.

Signing keys, private continuation files, downloaded toolchains, compiled outputs and large runtime binaries are excluded from Git. Runtime libraries belong in the prerelease asset, restored with `scripts/bootstrap_release_runtime.py`; corresponding source accompanies the binary. Keep the original private checkpoint separately when continuing development.

Verification after publishing must confirm public repository visibility, source commit/CI, release channel, every asset name/size/digest and actual download URLs. Do not describe publication as complete from local preparation alone.
