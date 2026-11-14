# Free-space symbol reference

The gallery contains 63 component symbols and 11 editable layouts. Drawings use common laboratory schematic conventions. They are not an ISO-certified symbol set or a ray-tracing model.

The geometry is drawn for this project. Reference conventions include the free-ray components in [PST-opTeXp](https://ctan.org/pkg/pst-optexp) and its [quick reference](https://mirrors.mit.edu/CTAN/graphics/pstricks/contrib/pst-optexp/pst-optexp-quickref.pdf). Cavity topology follows the usual [linear and ring resonator](https://www.rp-photonics.com/optical_resonators.html) distinction.

A three-port BS or PBS exposes the three channels used in the drawing; the omitted fourth channel is not a claim that a reciprocal optical beam splitter physically has only three modes. Ports have no enforced input/output direction.

Wave plates, filters, active media, and crystals use conventional outlines with identifying labels. Change the label for the actual material, retardance, wavelength, or function. Positive rotation is clockwise from each symbol’s original orientation.

The layouts contain ordinary editable components and connections. Their distances are schematic. Focal lengths, phase matching, coating spectra, cavity stability, losses, and polarization transformations are not calculated. Curved mirrors in the cavity layouts indicate focusing but do not specify radii.

Automatic mirror alignment uses the [law of reflection](https://www.physicsclassroom.com/mmedia/optics/lr.cfm) at the central surface port. The outward normal faces the two connected beam directions; a single direction means normal incidence at an end mirror. For curved symbols this uses the local normal at the vertex. Set a manual angle to disable Follow beams for that component. Other eligible components align their drawn port axes; this does not solve refraction, diffraction, or phase matching.

## Sources and detection

| Component | Initial label | Ports |
|---|---|---:|
| Laser | — | 1 |
| Broadband source | Source | 1 |
| Photodetector | — | 1 |
| Camera / CCD / CMOS | Camera | 1 |
| Optical power meter | PM | 1 |
| Viewing screen | Screen | 1 |
| Beam dump | Dump | 1 |

## Mirrors and beam splitters

| Component | Initial label | Ports |
|---|---|---:|
| Mirror at 45° | — | 1 |
| Plane mirror | — | 1 |
| Concave mirror | CM | 1 |
| Convex mirror | Convex M | 1 |
| Piezo mirror | PZT | 1 |
| Output coupler | OC | 2 |
| Cavity coupling mirror | OC | 1 |
| Beam splitter · 4 ports | — | 4 |
| Beam splitter · 3 ports | BS | 3 |
| Plate beam splitter · 3 ports | BS | 3 |
| Dichroic mirror · 3 ports | DM | 3 |

## Lenses and focusing

| Component | Initial label | Ports |
|---|---|---:|
| Converging lens | — | 2 |
| Diverging lens | — | 2 |
| Plano-convex lens | — | 2 |
| Plano-concave lens | — | 2 |
| Meniscus lens | — | 2 |
| Cylindrical lens | Cyl L | 2 |
| Aspheric lens | Asph L | 2 |
| Microscope objective | MO | 2 |
| Axicon | Axicon | 2 |

## Polarization

| Component | Initial label | Ports |
|---|---|---:|
| Linear polarizer | — | 2 |
| Half-wave plate | λ/2 | 2 |
| Quarter-wave plate | λ/4 | 2 |
| Variable retarder | LCVR | 2 |
| Polarizing BS · 4 ports | PBS | 4 |
| Polarizing BS · 3 ports | PBS | 3 |
| Glan–Thompson polarizer | GT | 2 |
| Wollaston prism | WP | 3 |
| Faraday rotator | FR | 2 |
| Optical isolator | ISO | 2 |

## Apertures and filters

| Component | Initial label | Ports |
|---|---|---:|
| Pinhole | PH | 2 |
| Variable iris | Iris | 2 |
| Slit aperture | Slit | 2 |
| Neutral-density filter | ND | 2 |
| Band-pass filter | BPF | 2 |
| Long-pass filter | LPF | 2 |
| Short-pass filter | SPF | 2 |
| Mechanical shutter | Shutter | 2 |
| Fabry–Pérot etalon | Etalon | 2 |

## Prisms and diffraction

| Component | Initial label | Ports |
|---|---|---:|
| Dispersive prism | Prism | 2 |
| Right-angle prism | RAP | 2 |
| Dove prism | Dove | 2 |
| Reflection grating | DG | 1 |
| Transmission grating | TG | 2 |
| Spatial light modulator | SLM | 2 |

## Nonlinear and active media

| Component | Initial label | Ports |
|---|---|---:|
| Second-order nonlinear crystal | χ⁽²⁾ | 2 |
| Noncollinear nonlinear crystal | χ⁽²⁾ | 3 |
| Periodically poled LiNbO₃ | PPLN | 2 |
| Third-order nonlinear medium | χ⁽³⁾ | 2 |
| Laser gain medium | Gain | 2 |
| Saturable absorber | SA | 2 |
| Acousto-optic modulator | AOM | 3 |
| Electro-optic modulator | EOM | 2 |
| Pockels cell | PC | 2 |
| Phase modulator | PM | 2 |
| Gas / vapor cell | Cell | 2 |

## Editable layouts

- Fabry–Pérot cavity
- Linear laser cavity
- Four-mirror ring cavity
- Bow-tie cavity
- Michelson interferometer
- Mach–Zehnder interferometer
- Sagnac interferometer
- Second-harmonic generation
- Noncollinear SPDC source
- Spatial filter / 4f relay
- Polarization preparation / analysis

Select **Cavities and layouts** in the gallery and drag a thumbnail onto the grid. The inserted components are selected together. Click blank canvas to clear the selection before dragging individual connection ports.
