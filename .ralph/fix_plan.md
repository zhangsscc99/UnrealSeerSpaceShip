# Fix Plan — enlarge the central Suzhou Garden to 4× ground area

## Goal

The **central walkable garden ground itself** becomes 4× larger in area, i.e.
**linear extent ×2 in X and Y**, with the terrain, paving, walls, building
clusters, pavilion spacing and waterways all laid out to match.

Scattering decorations further out to inflate the bounding box does **not** count
and has already been done once by mistake. The measure of success is the central
garden's own X/Y extent doubling.

## Safety net

Commit `c683096` is the known-good restored state (original water, original
landscape material, no greens, pink roofs kept). **Everything is recoverable from
it.** That is why you must commit each verified step as you go — a half-finished
garden must never be the only copy.

Never `git add -A`. Commit explicit paths.

---

## Phase 0 — Measure the baseline (do this first, record the numbers)

- [ ] 0.1 Find the centre of the **central garden**. Gather every actor's position,
      histogram the distance from candidate centres, and identify where the dense
      original garden ends and the outer ring / far decorations begin. Record the
      centre `C` and the current half-extent in X and Y in this file.
- [ ] 0.2 **Establish what the ground actually is.** Determine whether the central
      garden's walkable ground is the World Partition Landscape, discrete paving
      meshes, or both. Report: how many actors are Landscape proxies vs. paving
      static meshes, and which actor(s) provide the surface under the pavilions.
      Everything downstream depends on this — do not skip it.
- [ ] 0.3 Record the baseline actor census: total actors, static meshes, 30 pigs,
      0 `Grn_*`, and the Z range. Note any actor above z≈1200.
- [ ] 0.4 **Test whether the Landscape can be scaled at all.** Try a small scale
      change on `Landscape_UAID_A85E45CFE404FBD100_1221515703`, read it back, and
      undo it. Report whether the World Partition landscape accepts a transform
      scale, and whether the 64 proxies follow. If it does not, say so here — the
      approach changes and this is exactly the kind of thing worth discovering in
      loop 1 rather than loop 9.

## Phase 1 — Enlarge the ground

- [ ] 1.1 Scale the terrain to twice its X/Y linear extent about `C`.
      Keep it uniform per axis-pair as the asset allows; if the landscape resists
      scaling, stop and record the blocker rather than forcing it.
- [ ] 1.2 Enlarge the paving / ground meshes to cover the new extent, so there is
      no gap between the paving and the terrain behind it.
- [ ] 1.3 Verify: the ground's measured X/Y extent is ~2× baseline, and there is no
      hole or seam where the old garden edge used to be.

## Phase 2 — Respace the garden content

- [ ] 2.1 Move every actor of the **central garden** to `C + 2 × (old - C)` in X/Y.
      Use one batched script. Keep a record of every old→new transform.
- [ ] 2.2 Decide size vs. spacing per category and record the decision:
      pavilions, towers, corridors and walls keep their own size and spread out;
      long runs (walls, corridors, paving strips, banks) are scaled to span the
      larger gaps. **Never non-uniformly scale a mesh.**
- [ ] 2.3 Re-seat everything on the terrain: trace down at each new X/Y and set Z.
- [ ] 2.4 Verify: no actor floats above z≈1200; actor density over the enlarged
      ground looks comparable to before, not sparse or overlapping.

## Phase 3 — Waterways

- [ ] 3.1 Scale and reposition the water to match: `WaterZone_UAID_00163E6E452288F802_1311752325`,
      `Landscape_WaterBrushManager_0`, and the water surface meshes.
- [ ] 3.2 Keep the banks, the water surface and the water zone consistent with each
      other — a water plane that no longer meets its bank is a failure.
- [ ] 3.3 Verify the water still reads as water and that **`M_SG_Water` was not
      modified** (`git status` must not list it).

## Phase 4 — Pigs, sky and dressing

- [ ] 4.1 Re-seat the 30 pigs on the new ground so `BP_PigWander` still works and
      their wander centres are on solid ground.
- [ ] 4.2 Confirm sky/fog/lighting actors still make sense for the enlarged level.
- [ ] 4.3 Confirm dressing (rocks, plants, bamboo) is respaced with the rest and
      nothing is left straddling the old garden boundary.

## Phase 5 — Final verification and commit

- [ ] 5.1 Measure and record the final X/Y extent. It must be **~2× baseline**.
- [ ] 5.2 Confirm the constraints still hold: 0 `Grn_*` actors, landscape material
      still `/Game/Landscape/Materials/M_Landscape`, `M_SG_Water` untouched,
      pink-roof fix intact, 30 pigs on the ground.
- [ ] 5.3 `save_assets`, then commit the level changes with explicit paths and a
      message summarising the old and new extents.
- [ ] 5.4 Write the before/after numbers into this file so the next loop and the
      user can see what actually changed.

## Blockers / findings

Record anything that turned out to be impossible or different from the assumption
above. A well-evidenced "this cannot be done this way, here is what happens
instead" is a good loop, not a failed one.

- (none yet)
