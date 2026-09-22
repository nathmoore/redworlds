# Tape completion plan

**Started 2026-09-21.** This is the execution plan for taking all nine Region 3 tapes to at
least a numerically usable `provisional` state, then promoting each to `ready` where the
evidence supports it. [`backlog.md`](backlog.md) remains the authority for open modelling
questions; this file orders those questions into bounded implementation sessions.

The rule throughout is unchanged: a surprising or negative answer is a working result. We
do not alter model behaviour to make a tape beneficial or to make its cover equal the peg.

## Resume here — 2026-09-22 handoff

The table is operational: all nine tapes export, none is held, and every unresolved tape has
a numerical `provisional` result. The latest implementation slice replaces the shared road-
energy proxy for Remote Work and household EVs with reproducible, stressor-specific road
emissions. It is committed as `feat(emissions): derive household road combustion` alongside
the earlier Smart Grid, lifetime-cover and EV-forecourt commits.

Current headline results after the road change:

- Remote Work: −2.12 Gt CO₂e at its 700 M commuter-day/week ceiling; 183 M is a 1.000-brick
  cover; status remains provisional for commuting share, teleworkability and rebound.
- Household/private EV: −2.20 Gt CO₂e at the 320 M-car ceiling; **the cover was sized to the
  peg on 2026-09-22 at 80.8 M cars (1.000 brick)**, replacing the 11 M-car figure that
  measured 0.136. Sizing the cover is not tuning the result; the magnitude is expected to
  move again once the SSP2 grid and rebound land. Status remains provisional.
- Ban Gas: still uses the 27.4% physical-anchor proxy because EXIOBASE does not split
  household non-transport energy by fuel. This is the unfinished half of Milestone B.
- Smart Grid: −0.476 Gt at the selected 2% demand-response assumption; provisional.
- Product Lifetimes: exact +1-year cover is 3.352 bricks; ready mechanically, but its mean
  lives still need product-level evidence. Sizing it to one brick means a cover of about
  **three months** of added life (~0.258 yr), which is a game-side copy decision, not an
  engine change; the basket is unchanged at either magnitude.

Also landed 2026-09-22, after the road commit:

- the export states a `basis` object naming which fields carry which year — every tonne field
  is 2011 and the game applies `intensity_scalar_2050`, while `bricks_at_cover` and `copies`
  already carry it. One table held two bases with nothing on the fields to say so. This is the
  cheap half of the fix; the field names stay put because the game's PHP reads them, and the
  whole distinction disappears when the SSP2 walk replaces the scalar;
- EV's cover sized to the peg at 80.8 M cars (see Milestone C); and
- `docs/design/tape_records.md` corrected: its BUILD table still described geothermal as
  13 GW / 91 TWh and fusion as a 10-plant proxy, which are pre-`0aef774` covers.

Verification at handoff:

- ruff format/check and `ty check`: passed;
- fast suite: 174 passed before the final additional SWAP assertion; that assertion then
  passed in the focused action suite;
- strict documentation build: passed;
- nine-tape cached export: passed, with Remote Work at 0.9998 brick and EV at 0.136 brick;
- focused real-data road derivation: passed; and
- full `pytest -m integration`: **completed 2026-09-22 — 17 passed, 0 failed, 175 deselected,
  20:19** under `caffeinate -i`, uninterrupted and with no memory error. The 8 GB Intel Mac is
  a capable integration runner; the earlier 25:28 stop was planned sleep, not a limit.

Next work, in dependency order: (1) obtain a compatible Region 3 residential-gas activity
balance and finish Ban Gas `F_Y`; (2) run EV against the SSP2-walked grid and rebound
weightings; (3) optionally add commercial cars/vans/trucks as a separately reported `Z`/`F`
mechanism; (4) trace geothermal's coefficient; (5) source product-level mean lives; and
(6) complete the SSP2 baseline and uninterrupted integration run.

### Where tape choices should live

Do not create a second data source called `tape-choices`: committed executable choices stay
in `data/tech_choices/options.toml`, and `docs/design/tape_records.md` explains the shared
schema and current results. As evidence accumulates, a `docs/tapes/` directory with one
short evidence dossier per tape would be useful; those files should cite sources, sensitivities
and promotion gates while linking to — never duplicating — the TOML values. Create that
directory when the next tape-specific research result lands, beginning with Ban Gas. Keep
this file as the cross-tape execution/handoff view and `docs/backlog.md` as the authority for
open modelling decisions.

---

## What “working” means

A tape clears the minimum gate when:

1. its mechanism maps to named EXIOBASE rows and matrices;
2. it produces a signed numerical result from the cached baseline;
3. its money rule is preserved — BUILD moves money, SWAP keeps it, REDUCE removes it;
4. the export states whether the solve is at the cover or ceiling and gives an exact cover
   reading, or explicitly states why one needs a separate solve;
5. its physical ceiling and basis remain visible;
6. unit tests and the relevant cached-world integration test pass; and
7. any material unresolved assumption is exported as `status: provisional` with a named
   `limitation`.

`ready` means no known material tape-specific qualification remains. `Provisional` means
the result is usable for the MVP and honest about what could materially revise it. `Held`
means there is no numerical result. The first milestone below eliminates `held`; it does not
promise that every intervention abates.

---

## Starting position

| Tape | Current state | What remains |
|---|---|---|
| Buy Less | ready | No completion work |
| Extended Product Lifetimes | ready, exact +1-year cover solved | Source mean lives |
| Remote Work | provisional, road GHG resolved | Firm up commuting and teleworkable shares |
| Nuclear | ready | No completion work |
| Geothermal | provisional | Reconcile EXIOBASE’s 211 g CO₂e/kWh coefficient |
| Fusion | ready | No completion work; shares nuclear’s industrial ceiling |
| Electric Vehicle Transition | provisional, cover sized to the peg | 2050 grid and rebound sensitivity |
| Ban Gas Supply | provisional | Replace physical-anchor `F_Y` share with fuel-resolved direct GHG |
| Smart Grid | provisional, 0.86 brick | Strengthen the 2% demand-response evidence |

The current brick is the ten-reactor nuclear peg: **0.555 Gt CO₂e** after the 2050
intensity correction and real deployment curve.

---

## Milestone A — nine numerical tapes

This is the minimum requested outcome: eight existing numerical records plus Smart Grid,
with no tape left `held`.

### A1. Smart Grid: grid efficiency and demand response

**Decision made 2026-09-21:** Smart Grid means grid efficiency and demand response. It does
not include distributed solar, a generation-mix shift, or curtailment credit. Excluding
curtailment is necessary because this MRIO has no dispatch, capacity or hourly constraints
from which avoided curtailment could be derived.

The implementation is a pure A-matrix action, sampled at 0.25, 0.5, 0.75 and 1.0 deployment:

- For the Region 3 columns of *Transmission services of electricity* and *Distribution and
  trade services of electricity*, multiply all electricity-generation input coefficients by
  `(1 − 0.062) / (1 − 0.040) = 0.977083…` at full deployment. This represents losses falling
  from 6.2% to 4% while delivered electricity is unchanged.
- Apply the existing backlog’s conservative **2%** demand-response energy-saving assumption
  to generation and delivery inputs of other Region 3 industries. Also run 0% and 3% as a
  sensitivity. Do not apply demand response to the delivery columns a second time.
- Do not rescale the affected A columns back to their old totals: the missing input is the
  efficiency saving. Keep stressor intensities unchanged and rebuild the Leontief inverse.
- Do not add a Y-side solar purchase or claim the old 100 TWh curtailment component.

**Completed 2026-09-21.** The cached-world sensitivity is −0.074 Gt CO₂e with loss
reduction alone, −0.476 Gt at the selected 2% demand response (0.86 brick), and −0.677 Gt
at 3% (1.22 bricks). The record exports four deployment samples and remains provisional
because the 2% saving, not the implemented mechanism, needs firmer evidence. Its cover is
the full physical grid programme: the engine does not inflate it beyond 100% merely to make
the result equal one brick.

Record changes:

- change the ceiling from “220 TWh/yr losses and curtailment” to either `1.0` “fraction of
  the regional grid upgraded” or the loss-only physical headroom of approximately 120
  TWh/yr; prefer the fractional grid ceiling because demand response and loss reduction do
  not share one physical unit;
- retain the 6.2% → 4% loss assumptions and 2% demand-response assumption as explicit
  fields, not numbers buried in the action;
- set `status = "provisional"` until the coefficient sources and sensitivity are recorded;
  and
- derive the cover from the full solve without changing the physical ceiling.

Code shape:

- add a small pure action for the coefficient change;
- add a grid-tape runner with four deployment samples;
- dispatch the smart-grid record through that runner in the export; and
- reuse BUILD’s coefficient-recalculation path, but not BUILD’s generation substitution or
  construction capex.

Done when:

- full deployment lowers electricity required for the same delivery-sector output;
- 0% demand response isolates the loss result and 2% is better than 0%;
- the result is finite at all four deployment samples;
- no generation share moves toward solar or any other technology;
- the export contains a signed score, cover reading, `status: provisional` and limitation;
  and
- the money/output identities used by the coefficient path still hold.

### A2. Extended Product Lifetimes: solve the cover honestly

The ceiling solve is already working and `ready`. The missing export field is the +1-year
cover: demand removed is `N / (life + N)`, so the four-year ceiling cannot be divided by four.

Measured against the current approximate mean lives:

- **+1 year delivers 3.35 bricks**; and
- a one-peg cover would be **0.258 years, about 3.1 months**.

Implementation:

- store `mean_life_years` as data rather than recovering it from rounded four-year weights;
- derive product weights from `N / (mean_life_years + N)`;
- solve both the stated cover and ceiling explicitly; and
- export the actual `cumulative_at_cover_co2e_t` and `bricks_at_cover`.

This leaves a game-side calibration call visible rather than blocking the engine: keep a
meaningful +1-year cover worth 3.35 bricks, or use an approximately three-month one-peg
cover. The engine must not narrow the basket or weaken the result merely to reach one brick.

**Completed 2026-09-21.** `mean_life_years` now lives beside each applicable concordance
row, the four-year ceiling weights are derived at full precision, and the exporter runs a
separate one-year solve. The exact cover is **−4.248 Gt CO₂e on the 2011 basis**, or **3.352
bricks** after the 2050 intensity scalar. It is not the four-year result divided by four.
The approximate mean-life sources remain the promotion task; they do not block the honest
numerical endpoint.

Done when the export no longer reports `None` for this cover and a test proves that the
one-year result is not obtained by dividing the four-year result by four.

### A3. Regenerate and verify the complete table

- Export all nine records from a clean commit.
- Assert that there are no `held` records, exactly nine tape ids, and every provisional
  record has a non-empty limitation.
- Validate that a positive emissions delta produces zero abatement copies.
- Run the fast suite, strict docs build, all cached-world integration tests and the full
  EXIOBASE integration suite separately.

Suggested commits:

1. `feat(grid): model efficiency and demand response`
2. `feat(lifetimes): solve the nonlinear cover explicitly`
3. `docs(model): record the complete provisional tape table`

---

## Milestone B — retire shared direct-emissions proxies

Remote Work, EV and Ban Gas share one limitation: characterised household `F_Y` is regional,
not fuel-resolved. Fix it once rather than tuning three records independently.

### B1. Build a direct-household fuel-share input

- Derive road petrol/diesel and residential-gas combustion from Region 3 energy-carrier
  rows plus cited carrier-specific CO₂, CH₄ and N₂O factors, or from a compatible regional
  energy balance.
- Reconcile the apportioned components to EXIOBASE’s household direct CO₂ and GHG totals.
- Store the shares and provenance as committed input data.
- Keep the broad-basket default unchanged; only records naming a driver use a fuel share.

Done when shares are reproducible, lie in `[0, 1]`, do not overlap, reconcile within a stated
tolerance, and tests prove each tape changes only its attributed portion.

**Road component completed 2026-09-22.** Region 3 household `Energy Carrier Net TROA`
provides 7.940 EJ of road activity. The table's household petrol and diesel purchases imply
a 66.92% gasoline energy mix, used only to interpolate the close IPCC 2006 mobile-combustion
factors. This produces 575.7 Mt CO₂e and 562.8 Mt CO₂: 53.65% and 54.23% respectively of
the two characterised household-direct totals. The derivation is executable, row-specific
scaling is tested, and both Remote Work and EV now use it. Residential gas remains open
because the table's purpose rows do not identify non-transport energy by fuel; substituting
the gas-distribution sector's own energy input would mistake a margin sector for throughput.

### B2. Re-run Remote Work and Ban Gas

- Replace the 32.9% road-energy proxy and 27.4% gas physical-anchor proxy.
- Compare the new scores with the provisional ones and explain the movement.
- Promote each to `ready` only if no other material tape-specific limitation remains.

**Partial re-run completed 2026-09-22.** Remote Work now delivers −2.12 Gt CO₂e on the
2050-adjusted real curve at its ceiling, rather than −1.6 Gt. Its recalibrated one-brick
cover is 183 M avoided commuter-days per week. It remains provisional because the 30%
commuting share, 35% teleworkable share and rebound assumptions remain material. Ban Gas
awaits the regional residential-gas balance described above.

---

## Milestone C — settle the EV result

EV now abates under the provisional model after resolving direct tailpipe emissions. Four
known sensitivities define what is complete and what still prevents a `ready` result.

1. **Source purchase completeness.** Add *Retail trade services of motor fuel* as an avoided
   forecourt margin, but keep it out of the fuel-to-TJ conversion. Model source energy and
   its delivery margin separately, just as replacement generation and electricity delivery
   are separate now.
2. **Direct tailpipe GHG. Completed 2026-09-22.** Milestone B derives a 53.65% direct-CO₂e
   road share independently of the EV result. The old model changed sign near 41%, so this
   input was decision-relevant and was not selected to obtain the new sign.
3. **2050 electricity.** Re-run against the SSP2-walked 2050 table from GitHub issue #17.
   A uniform intensity scalar on the 2011 generation structure is particularly weak for an
   electrification tape.
4. **Rebound.** Report flat proportional re-spend and the documented income-elasticity
   weighting as a sensitivity. Do not silently select the one that makes EV beneficial.

Optional scope after those household sensitivities: extend electrification to commercial
cars, vans and trucks. That is not extra household demand; it needs a separate intermediate-
demand and industry-emissions (`Z`/`F`) mechanism, commercial fleet and vehicle-km ceilings,
and vehicle-class energy ratios. Keep its contribution separately reported so it cannot be
mistaken for evidence about the existing private-motoring tape.

**Source-margin item completed 2026-09-21.** The private-motoring basket now removes the
forecourt retail margin with petrol and diesel while `energy_source_products` keeps it out
of the TJ conversion. With the other provisional assumptions unchanged, the real cached
solve moves slightly from a +1.41 to a **+1.43 Gt CO₂e backfire**: the extra saving is
re-spent under SWAP’s closed-budget rule. The result was retained rather than tuned away.

**Direct-tailpipe item completed 2026-09-22.** With the independently derived road shares,
the full 320 M-car ceiling changes from a +1.43 Gt backfire to **−2.20 Gt CO₂e** on the
2050-adjusted real curve. The 11 M-car cover measured only **0.136 brick** in this model.

**Cover sized to the peg 2026-09-22 (Nathan).** The cover is now **80.8 M cars**, which
measures 1.000 brick, and the ceiling stays the physical fleet at 320 M. The solve is linear
in the fleet fraction, so this moves a game-side magnitude and leaves the physics untouched —
the discipline this file protects is against narrowing a basket or weakening a result to reach
a brick, not against sizing a cover to one. Two things follow. The ask is now a quarter of the
regional fleet, which is a much larger player-facing commitment than 11 M cars and should read
that way in the copy. And the magnitude is provisional in the same way the result is: EV is the
tape most exposed to the 2050 grid, so re-derive it when issue #17 lands and when rebound is
reported as a sensitivity. EV stays `provisional` until both do.

Retain the physical service ratio as a tested input and check it against vehicle-kilometre
energy data. After these runs:

- if EV abates robustly, calibrate its cover to the peg and promote it as evidence permits;
- if its sign depends on rebound or grid assumptions, keep it provisional and export the
  named dependency; or
- if it robustly backfires, retain zero abatement copies and return the intervention to the
  game as a finding rather than changing the engine.

Suggested commits:

1. `feat(emissions): apportion household combustion by fuel`
2. `fix(ev): separate fuel and forecourt spending`
3. `feat(baseline): walk the cached world to SSP2 2050`
4. `docs(model): record EV sensitivity and status`

---

## Milestone D — resolve remaining evidence limitations

These do not block a complete provisional table.

### D1. Geothermal coefficient

- Trace Region 3’s 211 g CO₂e/kWh through the unaggregated countries and stressor inputs.
- Determine whether it is composition, a known EXIOBASE allocation issue, or a label/unit
  problem.
- Compare against cited lifecycle literature without overwriting the database coefficient.
- Promote to `ready` only if the table value is explained; otherwise retain the table result
  and its provisional limitation.

### D2. Product lifetime evidence

- Check the eight mean lives against Vita et al. (2019) or a better product-level source.
- Re-run the +1- and +4-year points if the inputs change.
- Reconsider the four-year physical ceiling only from failure/replacement evidence, not game
  balance.

**Source audit started 2026-09-22.** Vita et al. supports the scenario mechanism and reports
the aggregate footprint potential of sharing and longer-lived clothes/devices, but the
article record does not provide the product-level service lives needed for `N/(life+N)`.
Treat it as a scenario cross-check, not as the source of the current 4/7/11/12-year inputs.
The next bounded task is a product-level source table for clothing, ICT, white goods,
medical/precision equipment and furniture; rerun both endpoints only after that table is
committed.

### D3. SSP2 and full integration

- Complete GitHub issue #17 so all tapes run on a real 2050 world rather than a 2011
  structure with an intensity scalar.
- Re-export every tape and compare rank, sign and cover against the provisional table.
- On the current 8 GB Intel Mac, run the full suite as a separate plugged-in task with other
  applications closed: `caffeinate -i just test -m integration`. The 2026-09-22 attempt
  reached 6 passes with no failures or memory error before being interrupted at 25:28 for
  planned computer sleep, so this machine appears capable but needs a window of at least
  40 minutes. A 16 GB+ machine remains the preferred future integration runner.

---

## Completion checklist

- [x] Smart Grid has a numerical provisional result and no solar/curtailment credit.
- [x] Extended Product Lifetimes has an exact cover solve.
- [x] All nine ids export; none is `held`.
- [ ] Every provisional record names the evidence needed for promotion.
- [ ] Household direct emissions are apportioned reproducibly by fuel (road complete; gas open).
- [ ] EV’s sign is tested against source margins, direct GHG, the 2050 grid and rebound.
- [ ] Geothermal’s coefficient is explained or explicitly retained as provisional.
- [ ] Mean product lives are sourced and the nonlinear cover is rerun.
- [ ] SSP2 2050 replaces the uniform intensity stand-in.
- [ ] Fast QA, cached integrations, strict docs and full EXIOBASE integrations pass.
