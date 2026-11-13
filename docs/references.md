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

> IPCC. (2021). Summary for Policymakers. In *Climate Change 2021: The Physical Science
> Basis. Contribution of Working Group I to the Sixth Assessment Report of the
> Intergovernmental Panel on Climate Change*. Cambridge University Press.
> https://www.ipcc.ch/report/ar6/wg1/

Used for the best estimate and likely range of warming per 1000 Gt CO₂ (0.45 °C, 0.27 to
0.63).

## Combustion emission factors

> IPCC. (2006). *2006 IPCC Guidelines for National Greenhouse Gas Inventories*, Volume 2:
> Energy, Chapter 3: Mobile Combustion, Tables 3.2.1 and 3.2.2.
> https://www.ipcc-nggip.iges.or.jp/public/2006gl/pdf/2_Volume2/V2_3_Ch3_Mobile_Combustion.pdf

Red Worlds uses the default road-transport CO₂, CH₄ and N₂O factors for motor gasoline and
gas/diesel oil. The characterised EXIOBASE GHG row uses IPCC 2007 GWP100, so CH₄ and N₂O are
converted with 25 and 298 respectively. The stationary-combustion chapter is the intended
factor source once a compatible Region 3 residential-gas activity balance is available:
https://www.ipcc-nggip.iges.or.jp/public/2006gl/pdf/2_Volume2/V2_2_Ch2_Stationary_Combustion.pdf

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
its 2010 level by 2025 — about −2.1%/yr compounded. Red Worlds uses the 0.73 directly for its
2011 → 2026 stage, which spans the same fifteen years.

> European Environment Agency. *Greenhouse gas emission intensity of electricity generation.*
> https://www.eea.europa.eu/en/analysis/indicators/greenhouse-gas-emission-intensity-of-1/greenhouse-gas-emission-intensity

EU electricity emission intensity fell 26% in the decade to 2024, reaching 213 g CO₂/kWh.
Recorded as context rather than used directly: consumption-based accounting makes the world
rate the relevant one, because most of a European footprint is imported.

> World Bank. *Carbon intensity of GDP.* Indicator EN.GHG.CO2.RT.GDP.KD.
> https://data.worldbank.org/indicator/EN.GHG.CO2.RT.GDP.KD

An alternative series for the same quantity, for anyone wanting to check the figure above
against a different compiler.

---

## The baseline walk (plan 03)

Sources for [`plans/03-baseline-walk.md`](plans/03-baseline-walk.md). Every entry below was
checked against the Crossref record for its DOI on 2026-11-11 (authors, year, title, journal,
pages). Links go to the publisher; several are paywalled.

**Walking an input-output table forward**

> De Koning, A., Huppes, G., Deetman, S., & Tukker, A. (2016). Scenarios for a 2 °C world: a
> trade-linked input–output model with high sector detail. *Climate Policy*, 16(3), 301–317.
> https://doi.org/10.1080/14693062.2014.999224

> Beaufils, T., & Wenz, L. (2022). A scenario-based method for projecting multi-regional
> input–output tables. *Economic Systems Research*, 34(4), 440–468.
> https://doi.org/10.1080/09535314.2021.1952404

> Dai, N., Liu, Q., Li, M., Malik, A., & Lenzen, M. (2024). Coupling an integrated assessment
> model with an input–output database. *Economic Systems Research*, 36(4), 527–544.
> https://doi.org/10.1080/09535314.2024.2387023

> Kikstra, J. S., Li, M., Brockway, P. E., Hickel, J., Keysser, L., Malik, A., Rogelj, J.,
> et al. (2024). Downscaling down under: towards degrowth in integrated assessment models.
> *Economic Systems Research*, 36(4), 576–606. https://doi.org/10.1080/09535314.2023.2301443

Wiebe et al. 2018, Cap et al. 2024, Vita et al. 2019, Bjelle et al. 2021, Södersten et al.
2018 and Ivanova & Wood 2020 are cited in full under *Scenario implementation in EE-MRIO*
above.

**The baseline scenario (CMIP7 Medium), the SSPs and long-term scenario models**

> O'Neill, B. C., Kriegler, E., Ebi, K. L., Kemp-Benedict, E., Riahi, K., Rothman, D. S.,
> van Ruijven, B. J., et al. (2017). The roads ahead: Narratives for shared socioeconomic
> pathways describing world futures in the 21st century. *Global Environmental Change*, 42,
> 169–180. https://doi.org/10.1016/j.gloenvcha.2015.01.004

> Riahi, K., van Vuuren, D. P., Kriegler, E., Edmonds, J., O'Neill, B. C., Fujimori, S.,
> Bauer, N., et al. (2017). The Shared Socioeconomic Pathways and their energy, land use, and
> greenhouse gas emissions implications: An overview. *Global Environmental Change*, 42,
> 153–168. https://doi.org/10.1016/j.gloenvcha.2016.05.009

> Van Vuuren, D. P., O'Neill, B. C., Tebaldi, C., Sanderson, B. M., Chini, L. P.,
> Friedlingstein, P., Hasegawa, T., et al. (2026). The Scenario Model Intercomparison Project
> for CMIP7 (ScenarioMIP-CMIP7). *Geoscientific Model Development*, 19(7), 2627–2656.
> https://doi.org/10.5194/gmd-19-2627-2026

Van Vuuren et al. 2026 defines the baseline's scenario, *Medium* (§3.3), and its path
beyond 2100 (§4).

> Hausfather, Z. (2026). Explainer: The CMIP7 emissions scenarios – and how they explore
> future climate change. *Carbon Brief*.
> https://www.carbonbrief.org/explainer-the-cmip7-emissions-scenarios-and-how-they-explore-future-climate-change

Used for Medium's headline figures (cumulative CO₂, warming in 2100 and its range, the
year 2 °C is passed), from a simple-climate-model ensemble on the published scenario data.

> KC, S., et al. (2024). *Updating the Shared Socioeconomic Pathways (SSPs) Global
> Population and Human Capital Projections*. IIASA Working Paper WP-24-003. Data: https://doi.org/10.5281/zenodo.7767425; 2025-rebased projections,
> https://doi.org/10.5281/zenodo.21738149 (CC BY 4.0).

The population half of SSP2 in its 2024/25 update. Full author list still to be taken from
the working paper.

> Armstrong McKay, D. I., Staal, A., Abrams, J. F., Winkelmann, R., Sakschewski, B.,
> Loriani, S., Fetzer, I., Cornell, S. E., Rockström, J., & Lenton, T. M. (2022). Exceeding
> 1.5 °C global warming could trigger multiple climate tipping points. *Science*,
> 377(6611), eabn7950. https://doi.org/10.1126/science.abn7950

Used for the warming thresholds named in the description of the 2050 world.

> Krey, V. (2014). Global energy-climate scenarios and models: a review. *WIREs Energy and
> Environment*, 3(4), 363–383. https://doi.org/10.1002/wene.98

> Jewell, J., & Cherp, A. (2023). The feasibility of climate action: Bridging the inside and
> the outside view through feasibility spaces. *WIREs Climate Change*, 14(5), e838.
> https://doi.org/10.1002/wcc.838

> Vaidyanathan, G. (2021). Integrated assessment climate policy models have proven useful,
> with caveats. *Proceedings of the National Academy of Sciences*, 118(9), e2101899118.
> https://doi.org/10.1073/pnas.2101899118

> Grubler, A., Wilson, C., Bento, N., Boza-Kiss, B., Krey, V., McCollum, D. L., Rao, N. D.,
> et al. (2018). A low energy demand scenario for meeting the 1.5 °C target and sustainable
> development goals without negative emission technologies. *Nature Energy*, 3(6), 515–527.
> https://doi.org/10.1038/s41560-018-0172-6

**Technology cost and maturity**

> Way, R., Ives, M. C., Mealy, P., & Farmer, J. D. (2022). Empirically grounded technology
> forecasts and the energy transition. *Joule*, 6(9), 2057–2082.
> https://doi.org/10.1016/j.joule.2022.08.009

- IEA (2026), *Energy Technology Perspectives 2026*, IEA, Paris. Licence: CC BY 4.0. Chapter 3
  holds the technology deployment dashboards; its technical notes define the market status
  categories used in the design doc. https://www.iea.org/reports/energy-technology-perspectives-2026
- IEA (2025), *World Energy Outlook 2025*, IEA, Paris. Licence: CC BY 4.0 for the report;
  CC BY NC SA 4.0 for Annex A, whose tables therefore cannot be committed here.
  https://www.iea.org/reports/world-energy-outlook-2025
- IEA (2023), *Net Zero Roadmap: A Global Pathway to Keep the 1.5 °C Goal in Reach* (2023
  update), IEA, Paris. Licence: CC BY 4.0.
  https://www.iea.org/reports/net-zero-roadmap-a-global-pathway-to-keep-the-15-0c-goal-in-reach
- IEA (2025), *Global Energy and Climate Model* documentation, "Understanding GEC Model
  scenarios" (the scenario definitions for the World Energy Outlook 2025).
  https://www.iea.org/reports/global-energy-and-climate-model/understanding-gec-model-scenarios
- IEA terms of use, which separate CC BY 4.0 reports from datasets and data annexes.
  https://www.iea.org/terms
- IAEA (2025), *World Fusion Outlook 2025*, including global deployment modelling by the MIT
  Energy Initiative. Cited for ranges only; figures quoted in the design doc are from
  summaries and are to be confirmed in the report. https://doi.org/10.61092/iaea.agh6-zpih
- IRENA (2025), *Renewable Power Generation Costs in 2024*. Cited for figures only; reuse
  terms not yet checked. https://www.irena.org/Publications/2025/Jun/Renewable-Power-Generation-Costs-in-2024

**Demographics and households**

> Chen, S., Huang, Q., Muttarak, R., Fang, J., Liu, T., He, C., Liu, Z., & Zhu, L. (2022).
> Updating global urbanization projections under the Shared Socioeconomic Pathways.
> *Scientific Data*, 9(1), 137. https://doi.org/10.1038/s41597-022-01209-5

> Ottelin, J., Heinonen, J., Nässén, J., & Junnila, S. (2019). Household carbon footprint
> patterns by the degree of urbanisation in Europe. *Environmental Research Letters*, 14(11),
> 114016. https://doi.org/10.1088/1748-9326/ab443d

> Rao, N. D., Sauer, P., Gidden, M., & Riahi, K. (2019). Income inequality projections for
> the Shared Socioeconomic Pathways (SSPs). *Futures*, 105, 27–39.
> https://doi.org/10.1016/j.futures.2018.07.001

**Food**

> Springmann, M., Clark, M., Mason-D'Croz, D., Wiebe, K., Bodirsky, B. L., Lassaletta, L.,
> de Vries, W., et al. (2018). Options for keeping the food system within environmental
> limits. *Nature*, 562(7728), 519–525. https://doi.org/10.1038/s41586-018-0594-0

> Poore, J., & Nemecek, T. (2018). Reducing food's environmental impacts through producers
> and consumers. *Science*, 360(6392), 987–992. https://doi.org/10.1126/science.aaq0216

> Zhao, J., Huang, J., & Nie, F. (2022). The Income Elasticities of Food, Calories, and
> Nutrients in China: A Meta-Analysis. *Nutrients*, 14(22), 4711.
> https://doi.org/10.3390/nu14224711

**Data sources**

- Ember, yearly electricity data by country and source. CC BY 4.0.
  https://ember-energy.org/data/electricity-data-explorer/
- PRIMAP-hist national historical emissions time series, **v2.6** (later versions are
  non-commercial). CC BY 4.0. https://zenodo.org/records/13752654
- JRC baseline projection by MR-GRAS. https://publications.jrc.ec.europa.eu/repository/handle/JRC120513
- IEA (2025), *Energy and AI*. Cited for figures only. https://www.iea.org/reports/energy-and-ai

