# Caveat emptor

Inkscape Optical Elements is experimental software for drawing free-space optical schematics. It is provided **as is**, under the warranty and liability terms in [LICENSE](LICENSE).

## What the drawings mean

The symbols follow common laboratory drawing conventions. They are not an ISO-certified symbol library, a complete catalog of optical devices, or a guarantee that a particular instrument is represented unambiguously. Supply labels and a legend appropriate to your experiment.

Automatic alignment adjusts eligible symbols to the connected line directions. It implements local mirror reflection and compatible port orientations. It does not perform ray tracing, wave propagation, optical design optimization, or experimental validation. A curved-mirror symbol uses the normal at its central vertex; it does not calculate focusing.

The extension does not calculate or verify focal lengths, imaging distances, aberrations, Gaussian beam parameters, diffraction, refraction, polarization transformations, phase matching, coherence, losses, coating spectra, cavity stability, tolerances, laser power, or damage thresholds. Layout templates are editable drawing starting points, not tested experimental prescriptions. Grid distances are schematic and do not specify physical lengths.

A three-port beam-splitter symbol shows three exposed drawing channels. It does not assert that a reciprocal optical beam splitter has only three physical modes. Ports do not enforce propagation direction. A bend in a right-angle connector does not create a real mirror. A single connected mirror direction is treated as normal-incidence return along that same path; the return beam is not drawn separately.

## User responsibility

Review connections, component labels, orientations, units, and exported figures before relying on or publishing them. The absence of an amber alignment warning is not evidence that a complete optical system is physically valid. Manual angles and unsupported device types are not validated by the alignment solver.

This drawing tool provides no laser-safety assessment, interlock design, or certification. Determine real apparatus requirements independently using appropriate optical design methods, manufacturer specifications, and applicable laboratory procedures.

Keep a backup of your SVG. The builder stores editable model data in the SVG. External edits to generated components or removal of this metadata can prevent reopening. PDF and PNG exports retain appearance, not the editable builder model.

## Compatibility and support

Version 0.6.0 is a pre-release. Development and regression checks used macOS, Inkscape 1.4.4, Python 3.14.7, and Tk 8.6. Windows, Linux, and other runtime combinations have not been validated for this release. Inkscape must use a Python interpreter with Tkinter. There is no bundled Python runtime, dependency installer, or automatic updater.

The extension performs local document editing. Its runtime contains no network requests, telemetry, or update checks. Like other Python extensions, it executes code with the permissions of the current user; read the included source and use a source you trust. No claim of a security audit is made.

No maintenance, response time, or fitness for a particular purpose is promised. The MIT license contains the controlling permission, warranty, and liability terms; this notice explains the intended scope and does not add restrictions to that license.
