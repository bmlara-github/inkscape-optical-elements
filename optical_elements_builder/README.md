# Optical Elements builder · 0.6.0

Copy this whole folder into the **User extensions** directory shown in Inkscape under **Preferences → System**, then restart Inkscape. Open **Extensions → Optical Elements → Build System…**.

Inkscape's selected Python needs **Python 3.9+ and Tkinter**. There is no bundled runtime or dependency installer. This pre-release was developed and checked on macOS with Inkscape 1.4.4, Python 3.14.7, and Tk 8.6. Windows, Linux, and other runtime combinations have not been validated.

Drag symbols onto the grid and drag between blue ports. Shift-click or drag a rectangle to select several components. Drag a selected component to move the selection. A port drag on a multiple selection moves the group; click blank canvas before connecting individual ports.

Mirrors and compatible port axes follow connected beams. **Align optics** restores automatic alignment for selected components, or all components when none are selected. Enter any finite rotation in **Angle °** and press **Set angle** for manual control; check **Follow beams** to restore automatic alignment for that component.

Choose **Apply to Inkscape**, save the SVG, then select the system and reopen the same menu to edit again. **Cancel** or closing the builder returns the original document. Keep the generated group and its metadata intact. Direct edits to individual generated paths or styles can block reopening, preserving those edits.

The full distribution contains `documentation/User_Guide.pdf`, a complete symbol reference, and editable examples. This folder alone is the installable extension. `optical_legacy.json` only supports reopening old drawings; the gallery contains free-space optics only.

Original project content is MIT-licensed. See **LICENSE**, **DISCLAIMER.md**, and **THIRD_PARTY_NOTICES.md** in this folder. The software is provided as is. Schematic alignment does not validate a physical optical system.

To update, close Inkscape, back up this folder and your SVGs, replace the folder, and restart. To uninstall, remove this folder and restart Inkscape.
