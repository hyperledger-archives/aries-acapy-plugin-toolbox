> **Note on plugin versions and ACA-Py**: To avoid a confusing pseudo-lock-step
> release, this plugin is versioned independent of ACA-Py. Plugin releases will
> follow standard [semver](semver.org) but each release will also be tagged with
> a mapping to an ACA-Py version with the format `acapy-X.Y.Z-J` where `X.Y.Z`
> corresponds to the ACA-Py version supported and `J` is an incrementing number
> for each new plugin release that targets the same version of ACA-Py.
>
> You should look for the most recent release tagged with the version of ACA-Py
> you are using (with the highest value for `J`).

# 0.1.0

## May 14, 2021

This marks the first official release of the Aries Cloud Agent - Python Toolbox
Plugin. This Plugin implements the protocols defined by the [Aries
Toolbox][aries-toolbox]. For details of the protocols added to ACA-Py by this
plugin, see the [Toolbox Documentation][toolbox-docs]

This version is compatible with ACA-Py 0.6.0.

[aries-toolbox]: https://github.com/hyperledger/aries-toolbox
[toolbox-docs]: https://github.com/hyperledger/aries-toolbox/tree/main/docs
