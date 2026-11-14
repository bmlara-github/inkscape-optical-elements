# Documentation

Read **User_Guide.pdf** for installation, a worked example, editing, alignment, troubleshooting, and licensing. **Symbol_Reference.md** lists all 63 symbols and 11 editable layouts.

The PDF source is **User_Guide.tex**. Its figures use the same vector geometry as the extension; blue connection ports and the dashed surface normal are guide annotations. They are not application screenshots.

To rebuild the PDF, use a LaTeX distribution with pdfLaTeX, Latin Modern, TikZ, microtype, geometry, fancyhdr, lastpage, tabularx, booktabs, enumitem, titlesec, and hyperref. From this documentation directory, run twice:

```sh
pdflatex -no-shell-escape -interaction=nonstopmode -halt-on-error User_Guide.tex
```

LaTeX is needed only to rebuild the guide. Neither it nor any PDF authoring tool is required by the extension. The project's documentation text and diagrams use the MIT license. Embedded Latin Modern font subsets retain the GUST Font License, included here together with the referenced LPPL 1.3c text.
