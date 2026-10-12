# Signing and update policy

Published engineering candidates and product1.0 retain the verified prototype development certificate for compatible prototype upgrades. The development keystore stays outside Git/public source archives. A fresh local build generates its own key if one is not supplied; that key cannot upgrade the published prototype in place. Export projects before uninstalling or switching certificates.

The SDK builder accepts --production only with an external CAD_SIGNING_KEYSTORE, CAD_SIGNING_ALIAS, CAD_STORE_PASSWORD and CAD_KEY_PASSWORD. It rejects project-local keys, missing credentials and the prototype certificate reused as production. Passwords are passed through environment references and are never release assets.

Product1.0 is a full GitHub release of the bounded mobile feature set, with debugging disabled and the retained development certificate. It does not establish a dedicated production signing identity or complete device qualification. Production identity/update migration and physical Android workflows remain pending. Public release notes must state the development identity and unclosed device/parity gates. No signing lineage is claimed. Modified libraries can be relinked and installed using a user's own certificate; corresponding source/build information accompanies binaries.
