# Units and currency — what is held in what, and where it converts

Four separate questions hide inside "what currency is this in", and conflating any two of
them produces a number that is wrong by a factor nobody can spot:

| Question | The two answers |
|---|---|
| **Which currency?** | EUR or USD |
| **Which year's money?** | 2011 or 2026 (inflation) |
| **Which price basis?** | basic (what the producer receives) or purchaser (what the buyer pays) |
| **Which year's physical world?** | 2011, 2027 or 2050 intensities and technology |

EXIOBASE answers the first three one way — **2011 basic-price million EUR** — and the game
needs the other end of all three. The fourth is not a currency question at all and is the one
most often mistaken for one; it lives in
[`engine/intensity.py`](../../src/redworlds/engine/intensity.py) and §4 below.

---

## 1. The chain

```
  2011 EXIOBASE table            the only measured thing in the chain
        │
        │  (a) correct the physical world 2011 → 2027   [observation]
        ▼
  2027 world                     emissions and energy mix as actually reported
        │
        │  (b) walk forward 2027 → 2050 along SSP2      [scenario]
        ▼
  2050 baseline                  the world the game's "now" sits in
        │
        │  (c) tape shock, solved, scored 2050–2100
        ▼
  deltas, in 2011 basic-price MEUR and kg CO2e
        │
        │  (d) convert money for display
        ▼
  2026 constant USD, purchaser prices
```

**(a) and (b) are physical; (d) is monetary.** They are independent: correcting the grid mix
does not change what a euro is worth, and converting euros to dollars does not change a
tonne. Keeping them in separate modules is deliberate.

**The physical pivot is 2027 and the money base year is 2026, and that mismatch is fine.**
They are answering different questions — what a euro emits versus what a euro buys — and
forcing them onto the same year would be cosmetic. The money year is fixed by the CPI series
`engine/currency.py` uses; the physical pivot is simply "now", where observation runs out.

**Money stays in 2026 constant USD throughout, including for 2050.** There is no further
inflation step between 2026 and 2050, and there should not be: the game shows a player what
a nuclear build *costs*, and "2026 dollars" is a unit they can feel. Inventing a 2050 price
level would add a made-up number and make every figure less legible, not more. So the
correct reading of a 2050 cost in this system is **"what this would cost if you bought it at
2026 prices"** — which is what a player understands by a dollar figure anyway.

---

## 2. Where each conversion lives

| Step | Module | Factor | Status |
|---|---|---|---|
| 2011 MEUR → 2026 MUSD | [`engine/currency.py`](../../src/redworlds/engine/currency.py) | ×2.072 (ECB 2011 EUR/USD 1.3917 × CPI ratio 1.489) | implemented, **unused by the tape path** |
| basic → purchaser | [`engine/prices.py`](../../src/redworlds/engine/prices.py) | ×1.20 universal markup | implemented, **unused by the tape path** |
| 2011 → 2027 intensity | [`engine/intensity.py`](../../src/redworlds/engine/intensity.py) | ×0.71 | **observed**, sourced |
| 2027 → 2050 intensity | same | ×0.62 | **scenario**, trend continuation standing in for SSP2 |

Combined money factor, 2011 basic MEUR → 2026 purchaser MUSD: **×2.49**.

**Two approximations ride on that 2.49 and should be stated wherever it appears.** The CPI
ratio is a projection, not a measurement — 2026 is not over. And the 1.20 markup is a
universal stand-in for EXIOBASE's TT and TTM matrices, which carry the real taxes and trade
and transport margins sector by sector; energy products are taxed far more heavily than 1.20
and services far less. A fuel tape's spend figure is therefore the least reliable monetary
number the engine produces.

---

## 3. The rule: convert at the edge, not in the middle

**Everything inside the engine is 2011 basic-price million EUR** — the table's own units,
untouched. The cached baseline, every intermediate system, every `gdp_impact` returned by
`engine/scoring.py`.

**Conversion happens once, in the export job, on the way out.** The exported table carries
2026 constant USD at purchaser prices, plus a `units` block naming every factor applied so a
consumer can back them out if a constant is later revised.

Three reasons this boundary is where it is:

1. **A converted table cannot be re-derived.** If the cache held converted values, revising
   the CPI figure would mean rebuilding the baseline — four minutes and a re-run of every
   tape. Converting at the edge makes a constant revision a one-line change and a re-export.
2. **Ratios are unit-free.** Emissions intensity per euro, the share of a basket, the
   fraction of household spend — none of these care which currency the denominator is in, so
   most of the engine never needs to know.
3. **One place to be wrong.** A factor applied in one function is checkable. The same factor
   applied in three jobs will eventually be applied twice in one of them.

> **Reconciliation note.** The game's Beta Day sheet (assumption X7, 2026-09-18) reads
> *"tape capex / spend stated in 2011 basic-price M.EUR inside the engine; the game's
> purchaser-price 2026 USD only ever appears in copy"* — that is, the engine never converts
> and the game does it when writing text. This doc keeps the first half exactly and moves the
> conversion into the export rather than into copy. The reason is that a number written in
> copy is converted by hand each time it is written, which is how two screens end up
> disagreeing; a number converted once in a job with a `units` block beside it cannot. The
> engine still never converts *internally*, so X7's substance is preserved.

---

## 4. The fourth question: which year's physical world

**This is not a currency conversion and must never be folded into one.** A euro removed in
2011 carries more carbon than a euro removed in 2050 will, because the grid is cleaner, coal
has left the mix and industry is more efficient. That is a change in kg CO₂e per euro, not in
what a euro is worth.

The correct treatment is to walk the table forward. Until that exists,
[`engine/intensity.py`](../../src/redworlds/engine/intensity.py) holds it as **two stages,
kept apart because they are different kinds of claim**:

```
2011 ──── observation ────▶ 2027 ──── scenario ────▶ 2050
          ×0.71                       ×0.62
```

- **2011 → 2027 is a matter of record.** The carbon intensity of world output fell about
  2.1% a year through the period — 27% below 2010 by 2025 — which compounds to 0.71 over
  sixteen years. Checkable against published series, and improvable without anyone agreeing
  about the future.
- **2027 → 2050 is a scenario.** The same rate run on, which is roughly what a
  middle-of-the-road SSP2 world does. Nobody can check it, and a real SSP2 run should replace
  it first.

They compose by multiplication, so the split costs nothing and buys two things: the observed
half can be replaced with real data long before the scenario half needs the full walk, and a
disagreement about the number can be localised to whichever half it is actually about.

**A world figure is used rather than a European one**, even though the tapes act on Region 3.
The accounting is consumption-based, so a European household's footprint is mostly the
intensity of the supply chains it buys from, and those are global. Region 3's own grid
decarbonised faster (EU electricity intensity fell 26% in the decade to 2024, to 213
gCO₂/kWh) but applying that rate would overstate how fast the imported half of the footprint
cleaned up.

**The split immediately paid for itself.** The single factor it replaced was 0.6, chosen for
being "about right". Decomposed, 0.6 implies the observed 0.71 followed by 0.85 — a
decarbonisation rate of 0.7%/yr after 2027, about a third of the 2.1%/yr actually being
managed before it. That is a substantive claim about the future that nobody had made
deliberately. Stated as two stages the arithmetic is visible; buried in one number it was
not. See [`../backlog.md`](../backlog.md).

---

## 5. Physical units

| Quantity | Unit | Where it comes from |
|---|---|---|
| Emissions, all-GHG | **kg CO₂ eq** | EXIOBASE `impacts`, characterised GWP100 row |
| Emissions, CO₂ only | **Gg** | EXIOBASE `impacts`, a different row **in different units** |
| Energy | TWh/yr, and kWh/day/person for ceilings | the tape records |
| Time | years, window 2050–2100 inclusive (51 years) | `engine/scoring.py` |

> ⚠ **The two emissions rows differ by 10⁶.** The all-GHG row is in kg CO₂ eq; the CO₂-only
> row is in Gg. Reading the second the way you read the first gives an answer a million times
> out, at magnitudes plausible enough to pass review. Read `impacts/unit.txt` per row.

> ⚠ **Never sum rows to get a total.** The `impacts` extension holds the same emissions
> several times over — a CO2EQ variant of the CO₂ row, two fuel-combustion rows nested inside
> it, and six GWP variants of the GHG total. Read one characterised row. The engine already
> does this correctly; the point is to keep it that way.

**Per-person units for ceilings.** Following MacKay, every ceiling carries a per-person
reading so it can be checked against his own stack (European consumption ~125 kWh/d/person).
See [`tape_records.md`](tape_records.md) §2.
