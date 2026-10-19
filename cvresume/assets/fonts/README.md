# PDF fonts

Noto Sans SC is distributed under the SIL Open Font License 1.1 in `OFL.txt`.

Source: https://github.com/notofonts/noto-cjk
Upstream file: `Sans/Variable/TTF/Subset/NotoSansSC-VF.ttf`

The regular (weight 400) and bold (weight 700) TrueType files here are static
instances of that upstream variable font, created using FontTools. They retain
the upstream character coverage and are embedded as subsets in generated PDFs.
Static instances avoid repeating variable-font instantiation for every resume.

These files are runtime application assets, not test outputs. They are loaded
relative to the Python module, independent of the server working directory.
