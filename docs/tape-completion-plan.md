# Tape completion plan

**Started 2026-09-21.** This is the execution plan for taking all nine Region 3 tapes to at
least a numerically usable `provisional` state, then promoting each to `ready` where the
evidence supports it. [`backlog.md`](backlog.md) remains the authority for open modelling
questions; this file orders those questions into bounded implementation sessions.

The rule throughout is unchanged: a surprising or negative answer is a working result. We
do not alter model behaviour to make a tape beneficial or to make its cover equal the peg.

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
| Extended Product Lifetimes | ready, ceiling solved | Exact +1-year cover solve; source mean lives |
| Remote Work | provisional | Replace road-energy share with fuel-resolved direct GHG |
| Nuclear | ready | No completion work |
| Geothermal | provisional | Reconcile EXIOBASE’s 211 g CO₂e/kWh coefficient |
| Fusion | ready | No completion work; shares nuclear’s industrial ceiling |
| Electric Vehicle Transition | provisional, currently backfires | Source margin, direct GHG share, 2050 grid and rebound sensitivity |
| Ban Gas Supply | provisional | Replace physical-anchor `F_Y` share with fuel-resolved direct GHG |
| Smart Grid | held | Implement the now-decided efficiency and demand-response mechanism |

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

Implement a pure A-matrix action, sampled at 0.25, 0.5, 0.75 and 1.0 deployment:

- For the Region 3 columns of *Transmission services of electricity* and *Distribution and
  trade services of electricity*, multiply all electricity-generation input coefficients by
  `(1 − 0.062) / (1 − 0.040) = 0.977083…` at full deployment. This represents losses falling
  from 6.2% to 4% while delivered electricity is unchanged.
- Apply the existing backlog’s conservative **2%** demand-response energy-saving assumption
  to electricity-generation inputs of other Region 3 industries. Also run 0% and 3% as a
  sensitivity. Do not apply demand response to the delivery columns a second time.
- Do not rescale the affected A columns back to their old totals: the missing input is the
  efficiency saving. Keep stressor intensities unchanged and rebuild the Leontief inverse.
- Do not add a Y-side solar purchase or claim the old 100 TWh curtailment component.

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

### B2. Re-run Remote Work and Ban Gas

- Replace the 32.9% road-energy proxy and 27.4% gas physical-anchor proxy.
- Compare the new scores with the provisional ones and explain the movement.
- Promote each to `ready` only if no other material tape-specific limitation remains.

---

## Milestone C — settle the EV result

EV currently backfires under the provisional model. This is a valid signed result, but four
known sensitivities must be resolved before treating the sign as robust.

1. **Source purchase completeness.** Add *Retail trade services of motor fuel* as an avoided
   forecourt margin, but keep it out of the fuel-to-TJ conversion. Model source energy and
   its delivery margin separately, just as replacement generation and electricity delivery
   are separate now.
2. **Direct tailpipe GHG.** Use Milestone B’s fuel-resolved road share. The present result
   changes sign at roughly a 41% road share, so this input is decision-relevant and must not
   be chosen to obtain a preferred sign.
3. **2050 electricity.** Re-run against the SSP2-walked 2050 table from GitHub issue #17.
   A uniform intensity scalar on the 2011 generation structure is particularly weak for an
   electrification tape.
4. **Rebound.** Report flat proportional re-spend and the documented income-elasticity
   weighting as a sensitivity. Do not silently select the one that makes EV beneficial.

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

### D3. SSP2 and full integration

- Complete GitHub issue #17 so all tapes run on a real 2050 world rather than a 2011
  structure with an intensity scalar.
- Re-export every tape and compare rank, sign and cover against the provisional table.
- On the current 8 GB Intel Mac, run the full suite as a separate plugged-in task with other
  applications closed: `caffeinate -i just test -m integration`. A 16 GB+ machine is the
  preferred future integration runner.

---

## Completion checklist

- [ ] Smart Grid has a numerical provisional result and no solar/curtailment credit.
- [ ] Extended Product Lifetimes has an exact cover solve.
- [ ] All nine ids export; none is `held`.
- [ ] Every provisional record names the evidence needed for promotion.
- [ ] Household direct emissions are apportioned reproducibly by fuel.
- [ ] EV’s sign is tested against source margins, direct GHG, the 2050 grid and rebound.
- [ ] Geothermal’s coefficient is explained or explicitly retained as provisional.
- [ ] Mean product lives are sourced and the nonlinear cover is rerun.
- [ ] SSP2 2050 replaces the uniform intensity stand-in.
- [ ] Fast QA, cached integrations, strict docs and full EXIOBASE integrations pass.
