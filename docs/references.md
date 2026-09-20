# References

---

## EXIOBASE 3

**Primary dataset citation:**

> Stadler, K., Wood, R., Bulavskaya, T., Södersten, C.-J., Simas, M., Schmidt, S.,
> Usubiaga, A., Acosta-Fernández, J., Kuenen, J., Bruckner, M., Giljum, S., Lutter, S.,
> Merciai, S., Schmidt, J. H., Theurl, M. C., Plutzar, C., Kastner, T., Eisenmenger, N.,
> Erb, K.-H., … Tukker, A. (2021). EXIOBASE 3 (3.8.2) [Data set]. Zenodo.
> https://doi.org/10.5281/zenodo.5589597

Red Worlds uses version 3.8.2, the `IOT_2011_pxp.zip` file (2011 product-by-product
monetary table), licensed [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).

**Methodological paper:**

> Stadler, K., Wood, R., Bulavskaya, T., Södersten, C.-J., Simas, M., Schmidt, S., …
> Tukker, A. (2018). EXIOBASE 3: Developing a Time Series of Detailed Environmentally
> Extended Multi-Regional Input-Output Tables. *Journal of Industrial Ecology*, 22(3), 502–515.
> https://doi.org/10.1111/jiec.12715

**Capital use matrices (for capital endogenisation):**

> Wood, R., & Södersten, C.-J. (2021). Capital use matrices (Version 3.8.2) [Data set].
> Zenodo. https://doi.org/10.5281/zenodo.7073276

Red Worlds uses the 2011 product-by-product file, `Kbar_exio_v3_8_2_2011_cfc_pxp.mat`
(consumption of fixed capital, flow form, million EUR), licensed
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The method is Södersten, Wood &
Hertwich (2018), cited below.

---

## pymrio

> Stadler, K. (2021). pymrio — Multi Regional Input-Output Analysis in Python.
> *Journal of Open Source Software*, 6(59), 3028.
> https://doi.org/10.21105/joss.03028

---

## Structural decomposition / MRIO methodology

> Wood, R., Stadler, K., Bulavskaya, T., Lutter, S., Giljum, S., de Schrijver, A., …
> Tukker, A. (2015). Global Sustainability Accounting — Developing EXIOBASE for
> Multi-Regional Footprint Analysis. *Sustainability*, 7(1), 138–163.
> https://doi.org/10.3390/su7010138

---

## Game design

Red Carbon game design by Nathan Moore. The engine design draws on:

> Schell, J. (2008). *The Art of Game Design: A Book of Lenses*. Morgan Kaufmann.

---

## Scenario implementation in EE-MRIO (harvested from the Red Carbon literature review, 2026-09)

> Wiebe, K. S., Bjelle, E. L., Többen, J., & Wood, R. (2018). Implementing exogenous
> scenarios in a global MRIO model for the estimation of future environmental footprints.
> *Journal of Economic Structures*, 7, 20. https://doi.org/10.1186/s40008-018-0118-y
> Code and data: https://doi.org/10.5281/zenodo.1342557

> Cap, S., de Koning, A., Tukker, A., & Scherer, L. (2024). (In)Sufficiency of industrial
> decarbonization to reduce household carbon footprints to 1.5°C-compatible levels.
> *Sustainable Production and Consumption*, 45, 216–227.
> https://doi.org/10.1016/j.spc.2023.12.031

> Vita, G., Lundström, J. R., Hertwich, E. G., Quist, J., Ivanova, D., Stadler, K., &
> Wood, R. (2019). The environmental impact of green consumption and sufficiency
> lifestyles scenarios in Europe: Connecting local sustainability visions to global
> consequences. *Ecological Economics*, 164, 106322.
> https://doi.org/10.1016/j.ecolecon.2019.05.002

> Wood, R., Moran, D., Stadler, K., Ivanova, D., Steen-Olsen, K., Tisserant, A., &
> Hertwich, E. G. (2018). Prioritizing consumption-based carbon policy based on the
> evaluation of mitigation potential using input-output methods. *Journal of Industrial
> Ecology*, 22(3), 540–552. https://doi.org/10.1111/jiec.12702

> Bjelle, E. L., Wiebe, K. S., Többen, J., Tisserant, A., Ivanova, D., Vita, G., &
> Wood, R. (2021). Future changes in consumption: The income effect on greenhouse gas
> emissions. *Energy Economics*, 95, 105114. https://doi.org/10.1016/j.eneco.2021.105114

> Södersten, C.-J., Wood, R., & Hertwich, E. G. (2018). Endogenizing capital in MRIO
> models: The implications for consumption-based accounting. *Environmental Science &
> Technology*, 52(22), 13250–13259. https://doi.org/10.1021/acs.est.8b02791

> Simas, M., Wood, R., & Hertwich, E. (2015). Labor embodied in trade: The role of labor
> and energy productivity and implications for greenhouse gas emissions. *Journal of
> Industrial Ecology*, 19(3), 343–356. https://doi.org/10.1111/jiec.12187

> Ivanova, D., & Wood, R. (2020). The unequal distribution of household carbon footprints
> in Europe and its link to sustainability. *Global Sustainability*, 3, e18.
> https://doi.org/10.1017/sus.2020.12

## Climate physics and scoring metric

> Allen, M. R., Friedlingstein, P., Girardin, C. A. J., Jenkins, S., Malhi, Y., Mitchell-
> Larson, E., Peters, G. P., & Rajamani, L. (2022). Net zero: Science, origins, and
> implications. *Annual Review of Environment and Resources*, 47, 849–887.
> https://doi.org/10.1146/annurev-environ-112320-105050

## Register and method for sizing interventions

> MacKay, D. J. C. (2008). *Sustainable Energy — Without the Hot Air*. UIT Cambridge.
> https://www.withouthotair.com/

## Tape sizing — external figures

These do not come from the IO table. They convert a tape's real-world cover magnitude into
a fraction of a product basket, so they sit in `data/tech_choices/options.toml` as a
`regional_ceiling_basis` and are only as good as the source. See `docs/backlog.md`
§Tape sizing figures for the work item to firm them up.

> Dingel, J. I., & Neiman, B. (2020). How many jobs can be done at home?
> *Journal of Public Economics*, 189, 104235. https://doi.org/10.1016/j.jpubeco.2020.104235

37% of US jobs can be performed entirely at home. The replication code and the
occupational classification are at https://github.com/jdingel/DingelNeiman-workathome.

> Sostero, M., Milasi, S., Hurley, J., Fernández-Macías, E., & Bisello, M. (2020).
> *Teleworkability and the COVID-19 crisis: a new digital divide?* JRC Working Papers
> Series on Labour, Education and Technology 2020/05. European Commission, Seville.

Applies the Dingel–Neiman classification to Europe and reaches the same 37% for EU
dependent employment. Red Worlds shades this to ~35% for Region 3, which also contains
middle-income economies that Dingel & Neiman's cross-country extension scores lower.

> Eurostat. *Passenger mobility statistics.* Statistics Explained.
> https://ec.europa.eu/eurostat/statistics-explained/index.php?title=Passenger_mobility_statistics

Commuting is the largest single reason for daily distance travelled, ranging from 27% of
daily distance in Germany to 47% in Croatia. Red Worlds uses ~30% for commuting's share of
household car distance, at the low end deliberately: annual distance carries more
long-distance leisure travel than daily distance does.

## Emissions intensity over time

Behind the two-stage correction in `src/redworlds/engine/intensity.py`. The observed stage is
citable; the scenario stage is a trend continuation and has no source by construction.

> Enerdata. *World CO₂ intensity of GDP.* Global Energy & CO₂ Data yearbook.
> https://yearbook.enerdata.net/co2/world-CO2-intensity.html

Global CO₂ intensity of GDP fell an average of 2.2% a year over 2010–2019 and stood 27% below
its 2010 level by 2025 — about −2.1%/yr compounded, which is the rate Red Worlds uses for
2011 → 2027.

> European Environment Agency. *Greenhouse gas emission intensity of electricity generation.*
> https://www.eea.europa.eu/en/analysis/indicators/greenhouse-gas-emission-intensity-of-1/greenhouse-gas-emission-intensity

EU electricity emission intensity fell 26% in the decade to 2024, reaching 213 g CO₂/kWh.
Recorded as context rather than used directly: consumption-based accounting makes the world
rate the relevant one, because most of a European footprint is imported.

> World Bank. *Carbon intensity of GDP.* Indicator EN.GHG.CO2.RT.GDP.KD.
> https://data.worldbank.org/indicator/EN.GHG.CO2.RT.GDP.KD

An alternative series for the same quantity, for anyone wanting to check the figure above
against a different compiler.

