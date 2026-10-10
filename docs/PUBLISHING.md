# Publish nln41-pi-airprint on GitHub

The recommended repository name is **nln41-pi-airprint**.
Display title: **NefLaca NL-N41 Pi AirPrint**.
Suggested description:

> Independent ARM64 CUPS driver and Pi installer for NefLaca NL-N41 USB thermal label printers, with AirPrint sharing and default grayscale rendering.

No repository, account, publication or upload has been created for you.

## Prepare the folder

Extract the source release ZIP. Upload the **contents** of the extracted
nln41-pi-airprint-v0.6.2 folder so README.md is at the repository root.
It contains src/, ppd/, scripts/, tests/, docs/, bin/, packages/, Makefile,
LICENSE, SHA256SUMS, .gitignore and .gitattributes. The install ZIP belongs in
packages/ and Release assets; uploading just that ZIP does not expose browsable
source code. Earlier private workspace outputs/vendor files are not part of
this release folder.

## Website method

1. Sign in to GitHub. Choose **+ > New repository**. Name it nln41-pi-airprint,
   select Public and enter the description above. Leave generated README,
   license and .gitignore unchecked because this folder supplies them.
2. On the empty repository use **uploading an existing file**, or **Add file >
   Upload files** when available. Drag the release folder's contents, preserving
   its subdirectories. Check README.md is at the root, then commit the upload.
3. Finder hides dotfiles by default: Command-Shift-Period shows .gitignore and
   .gitattributes. Include them; the Git method below preserves modes more
   reliably than browser uploads.
4. Open **Releases > Draft a new release**. Create tag **v0.6.2**, target the
   uploaded main branch, and title it **NefLaca NL-N41 Pi AirPrint v0.6.2**.
5. Paste [RELEASE-NOTES.md](RELEASE-NOTES.md). Attach these unchanged files from
   packages/: **nln41-pi-airprint-v0.6.2.zip**, **nln41-pi-airprint-v0.6.2.run**
   and **SHA256SUMS**. Publish the release when ready.

Official steps: [create a repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository),
[upload files](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository),
[manage releases](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository).

## Git method

Create an empty repository on your account, then open a terminal in the source
release folder. Replace YOUR_ACCOUNT before running:

```sh
git init
git add .
git commit -m "Publish NefLaca NL-N41 Pi AirPrint v0.6.2"
git branch -M main
git remote add origin https://github.com/YOUR_ACCOUNT/nln41-pi-airprint.git
git push -u origin main
git tag v0.6.2
git push origin v0.6.2
```

Use your normal GitHub authentication. The commands are instructions, not
commands already executed here. If you already published an earlier version,
update the existing checkout rather than repeating git init/remote add. Create
and attach the Release assets in the website as above.

## Verify the published result

Check the root README renders, the src/ C file can be browsed, and the Release
provides the Pi ZIP/.run plus checksum. Download those Release assets into a
clean folder; from that folder run `sha256sum -c SHA256SUMS` on Linux or
`shasum -a 256 -c SHA256SUMS` on a Mac. Download both listed assets for this check.
The GitHub-generated Source code ZIP is the repository snapshot, whereas the
attached Pi ZIP is the ready-to-install package. Tell end users to download
**nln41-pi-airprint-v0.6.2.zip**.

Future releases: change version strings, update test evidence, rebuild the
ARM64 filter only if its source changes, and run `python3 scripts/build-release.py`.
Recheck privacy/manifests and use a new tag; do not silently replace a published
asset while retaining its previous checksum. README.md explains the project motivation and identifies the tested printer
brand/model. This release uses English-only documentation.
