# NAP satiksmes dati → /api/celi un /api/satiksme

Avots: Nacionālais piekļuves punkts transportdata.gov.lv (VSIA „Latvijas Valsts ceļi”), visas kopas **CC0 1.0**
(DCAT `metadata_dcat/<nr>`). Lejupielāde: `POST https://www.transportdata.gov.lv/api/v1/get/file/download-file`,
ķermenis `{"file_id": "1", "format": "xml"}`, galvene `x-api-key` (katrai kopai sava atslēga). 204 = plūsma tukša.
Visas kopas ir DATEX II v3. Kods: `src/karte/api/karte_api.py`, sadaļas „Ceļu slēgumi un negadījumi” un „Satiksme zonās”.

## Atslēgas (VPS `/etc/hakatons/map.env`) → kopas

| Vides mainīgais | NAP kartīte (DCAT nr.) | Kopa | Publikācija | Kur lieto |
|---|---|---|---|---|
| `NAP_API_KEY_NEGADIJUMI` | e8659cdd (126) | Negadījumi un starpgadījumi | SituationPublication | /api/celi `negadijums` |
| `NAP_API_KEY_REMONTI` | 35fa5c41 (17977) | Remontdarbi | SituationPublication | /api/celi `remonts` |
| `NAP_API_KEY_SATIKSME_SLIDENS` | f3204a64 (10) | Īslaicīgi slidens ceļš (SIC) | SituationPublication | /api/celi `slidens`, /api/satiksme `stacijas` |
| `NAP_API_KEY_UZTURETAJI_SLIDENS` | 6749e127 | Īslaicīgi slidens ceļš (uzturētāji) | SituationPublication | tas pats |
| `NAP_API_KEY_METEO_SLIDENS` | 46cd2e45 (28623) | Īslaicīgi slidens ceļš (meteostacijas, CMS) | SituationPublication | tas pats |
| `NAP_API_KEY_SATIKSMES_IEKARTU_MERIJUMI` | fef717ac (279) | Satiksmes uzskaites iekārtu atrašanās vietas | MeasurementSiteTablePublication | /api/satiksme vietas |
| `NAP_API_KEY_SATIKSMES_APJOMS_ATRUMS_MIN` | ed1f0d2c | Satiksmes intensitāte un ātrums (minūtes) | MeasuredDataPublication (pieņemts) | /api/satiksme zonas |
| `NAP_API_KEY_ROBEZAS_LAIKS` | cb730ba2 (292) | Robežšķērsošanas gaidīšanas laiks | nav parauga | /api/satiksme `robezas` |
| `NAP_API_KEY_SLEGUMI`, `NAP_API_KEY_JOSLAS` | 75611a36, 82e20567 | Ceļu slēgumi, joslu slēgumi | — | nav abonēts; bez atslēgas izlaiž |

## Lauki (lokālie vārdi; `ET.iter` neprot `{*}`, tāpēc meklē pēc vārda)

**SituationPublication** (`situationRecord`): `id` atribūts; `xsi:type` (piem., `EnvironmentalObstruction`,
`ConstructionWorks`, `WeatherRelatedRoadConditions`); `validityStatus` (`suspended` izlaiž); `overallStartTime`,
`overallEndTime`, `situationRecordVersionTime`; teksts `generalPublicComment/…/value[@lang]` (negadījumu plūsmā teksta
nav — aprakstu veido no kodiem: `environmentalObstructionType`, `weatherRelatedRoadConditionType`,
`nonWeatherRelatedRoadConditionType`, `constructionWorkType`, `roadMaintenanceType`, `trafficConstrictionType`,
`temporarySpeedLimit`); kavējums `impact/delays/delayTimeValue` (s); vieta — visi `openlrCoordinates/latitude|longitude`
(`openlrLinear/firstDirection/openlrLocationReferencePoint`… līnijām, `openlrPointLocationReference` punktiem).

**MeasurementSiteTablePublication** (279): `measurementSite@id` + `measurementSiteLocation/coordinatesForDisplay/
latitude|longitude`. Nosaukuma nav. Kartītes paraugā (`NPP_DK_Paraugs_279.xml`) platums un garums ir samainīti vietām —
parsētājs to labo (ja „platums” ir 20–29 un „garums” 55–59). Īstajā plūsmā 77 iekārtas.

**MeasuredDataPublication** (minūšu kopa; **parauga vēl nav**, parsētājs pēc DATEX II v3 standarta):
`siteMeasurements/measurementSiteReference@id` (sasaista ar 279), `measurementTimeDefault`, ātrums
`averageVehicleSpeed/speed` (km/h, svērts ar `@numberOfInputValuesUsed`), plūsma `vehicleFlow/vehicleFlowRate`
(transp./h), arī `travelTime/duration` (s) robežām. Ja īstā plūsma atšķiras — labot `_datex_merijumi`.

**Robežas**: parauga nav. Parsētājs pieņem vai nu situācijas ar `delayTimeValue`, vai mērījumus ar `travelTime/duration`.

## Zonas un līmenis

- Iekārta → zona: `regioni` (novads vai valstspilsēta, `ST_Contains`); ja datubāze nav pieejama — ~10 km režģis
  (`rezgis_<i>_<j>`, 0,09° × 0,15°). Zonas `bbox` ir abos gadījumos; pašvaldības robeža: `/api/regioni/<kods>`.
- Līmenis iekārtā: vidējais ātrums / brīvas plūsmas ātrums: ≥ 0,75 brīvs (0), ≥ 0,5 lēns (1), citādi sastrēgums (2);
  bez mērījuma — nav datu (3). Zonā — ar plūsmu svērts vidējais.
- Brīvas plūsmas ātrums: lielākais API procesā redzētais vidējais ātrums iekārtā (≤ 130), kad ir ≥ 5 mērījumi;
  līdz tam 80 km/h. Atļautā ātruma kopa (ātruma zīmes 0d9dbc43) nav abonēta.
- Temperatūras (`cela_temp`, `gaisa_temp`) slidenā ceļa kopās nav; tās būtu kopā „Meteostaciju reāllaika mērījumi”
  (5a1e9a81), kas nav abonēta — lauki ir `null`.

Paraugi (saīsināti): `notes/research/paraugi/nap_*.xml`.
