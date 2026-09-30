# S mark

A vector trace of the original halftone "S". Every dot is detected at its exact position and size in the reference image, and the crescents and blades are traced from their edges. The result is the original image as clean, scalable vector.

| File | Use |
|---|---|
| `s-mark.svg` / `.png` | Primary. Gradient, transparent background |
| `s-mark-on-dark` / `s-mark-on-light` | On `#0E0F12` / on `#F4F1EC` |
| `s-mark-flat`, `-white`, `-black` | Flat colours and one-colour versions |
| `s-mark-app-icon` | Square, on dark |
| `showcase.png` | Presentation frame |

Colours: copper `#C9603A` / `#E5825B` / `#F4AA84`, teal `#1E9FAC` / `#43C4CB` / `#78E2DE`.

Regenerate: `cd src && python3 export.py ..`. `trace.npy` holds the traced geometry. `trace.py` re-traces it from the reference image and needs `numpy scipy scikit-image pillow`.
