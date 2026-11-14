# Third-party notices and references

The project's original Python source, JSON symbol and layout data, SVG examples, and documentation are distributed under the MIT license in [LICENSE](LICENSE). Third-party software and fonts retain their own licenses. No rights in third-party names or trademarks are granted by this project.

## Runtime software, installed separately

- **Inkscape** is the host application and is not bundled. It is free software under its own GNU GPL terms. See [Inkscape licensing](https://inkscape.org/about/license/).
- **Python**, including the standard-library modules used here, is installed separately. See [Python licensing](https://docs.python.org/3/license.html).
- **Tkinter / Tcl / Tk** provides the editor window and is supplied by the selected Python installation. Tcl/Tk is not bundled. See the Tcl/Tk notices supplied with that installation and the [Tcl/Tk license](https://www.tcl-lang.org/software/tcltk/license.html).

This extension is an independent project. It is not an official Inkscape product and is not endorsed by the Inkscape project or the reference authors below.

## Drawing references

The SVG geometry and layouts were drawn for this project. The following resources informed schematic conventions and explanations; their source code, illustrations, and manuals are not copied into the extension.

- Christoph Bersch, **PST-opTeXp**, [CTAN package](https://ctan.org/pkg/pst-optexp) and [quick reference](https://mirrors.mit.edu/CTAN/graphics/pstricks/contrib/pst-optexp/pst-optexp-quickref.pdf). The upstream package uses LPPL 1.3c or later; that license applies to the upstream work, which is not bundled here.
- Rüdiger Paschotta, **Optical Resonators**, [RP Photonics Encyclopedia](https://www.rp-photonics.com/optical_resonators.html). Reference for linear and ring cavity terminology.
- **The Law of Reflection**, [The Physics Classroom](https://www.physicsclassroom.com/mmedia/optics/lr.cfm). Reference for the local reflection rule used in schematic alignment.
- **My first effect extension**, [official Inkscape extension documentation](https://inkscape.gitlab.io/extensions/documentation/tutorial/my-first-effect-extension.html). Reference for the user extensions directory and effect mechanism.

## Preparation tools and PDF fonts

The development workflow uses **fontTools** to precompute polylines from the project's own SVG paths. fontTools is MIT-licensed and is not included or required at runtime. See its [license](https://github.com/fonttools/fonttools/blob/main/LICENSE). The distributed JSON previews are geometry derived from this project's own drawings.

The PDF guide was typeset with LaTeX/TikZ and **Latin Modern** fonts. These tools are not needed to use the extension or read the PDF. Embedded Latin Modern font subsets retain the **GUST Font License**. Latin Modern copyright is 2003-2021 B. Jackowski and J. M. Nowacki on behalf of TeX Users Groups, based on Computer Modern by Donald E. Knuth. The full documentation distribution includes `documentation/GUST-FONT-LICENSE.txt`; upstream information is available from the [GUST font project](https://www.gust.org.pl/projects/e-foundry/latin-modern/).

No standalone third-party font files, Inkscape binaries, Python runtime, or Tcl/Tk libraries are included in the installable extension folder.
