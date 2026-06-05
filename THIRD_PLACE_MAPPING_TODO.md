# Annex C Mapping TODO

The current prototype uses `wm_tippspiel.engine._assign_third_place_groups` as a constraint-based resolver.

For production-grade exactness, replace it with a literal lookup of FIFA Regulations Annexe C:

- key: sorted string of the eight qualified third-place groups, e.g. `EFGHIJKL`
- value: mapping for the eight winner slots `1A,1B,1D,1E,1G,1I,1K,1L`

Then translate those winner slots back to the R32 refs:

- `1E` -> `3ABCDF` / match 74
- `1I` -> `3CDFGH` / match 77
- `1A` -> `3CEFHI` / match 79
- `1L` -> `3EHIJK` / match 80
- `1D` -> `3BEFIJ` / match 81
- `1G` -> `3AEHIJ` / match 82
- `1B` -> `3EFGIJ` / match 85
- `1K` -> `3DEIJL` / match 87
