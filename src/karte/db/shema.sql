-- Kartes datubāze `map` (PostgreSQL 16 + PostGIS) uz VPS. Droši palaist atkārtoti.
-- Palaišana (VPS): psql "$MAP_DB_OWNER_DSN" -v ON_ERROR_STOP=1 -f src/karte/db/shema.sql
-- Ģeometrijas glabājam WGS-84 (EPSG:4326); attālumus rēķinām caur geography (metros).

-- Pašvaldības (35 novadi + 7 valstspilsētas) un pilsētas (VZD adrešu reģistrs, aw_shp.zip).
create table if not exists regioni (
  kods        text primary key,                 -- VZD adrešu reģistra kods
  atvk        text,                             -- ATVK kods, ja ir
  nosaukums   text not null,
  tips        text not null check (tips in ('valstspilseta', 'novads', 'pilseta')),
  novads_kods text,                             -- pilsētai: novads, kurā tā atrodas
  geom        geometry(MultiPolygon, 4326) not null,
  geom_vienk  geometry(MultiPolygon, 4326) not null,  -- vienkāršota (~50 m) rādīšanai kartē
  atjaunots   timestamptz not null default now()
);
create index if not exists regioni_geom_idx on regioni using gist (geom);

-- Slāņi kartē. grupa: patvertnes | infrastruktura | incidenti (filtrā rāda pa grupām).
create table if not exists kategorijas (
  kods      text primary key,
  nosaukums text not null,
  grupa     text not null,
  krasa     text not null default '#57534e',
  kartiba   int  not null default 100
);

insert into kategorijas (kods, nosaukums, grupa, krasa, kartiba) values
  ('patvertne',  'Publiskās patvertnes',     'patvertnes',     '#b91c1c', 10),
  ('neatliekama_24h', 'Neatliekamā palīdzība 24/7 (slimnīcas)', 'veseliba', '#7c3aed', 15),
  ('slimnica',   'Slimnīcas un ārstniecības iestādes', 'veseliba', '#be185d', 16),
  ('aptieka',    'Aptiekas',                 'veseliba',       '#15803d', 17),
  ('bankomats',  'Bankomāti',                'infrastruktura', '#1d4ed8', 20),
  ('policija',   'Policija',                 'infrastruktura', '#1e3a8a', 50),
  ('ugunsdzeseji', 'Ugunsdzēsēji (VUGD)',    'infrastruktura', '#c2410c', 60),
  ('degviela',   'Degvielas uzpildes stacijas', 'infrastruktura', '#a16207', 70),
  ('udens_limenis', 'Ūdens līmenis upēs un ezeros (LVĢMC)', 'vide', '#0891b2', 80)
on conflict (kods) do update set
  nosaukums = excluded.nosaukums, grupa = excluded.grupa, krasa = excluded.krasa, kartiba = excluded.kartiba;

-- Datu avoti. Katram objektam jābūt avotam no šīs tabulas; karte tos rāda sadaļā "Datu avoti"
-- un katra punkta logā. atverts = false: avotam nav norādīta atvērta licence (karte to brīdina).
create table if not exists avoti (
  kods          text primary key,
  nosaukums     text not null,
  izdevejs      text not null,
  licence       text not null,
  licences_url  text,
  atverts       boolean not null,
  datu_kopa_url text,                 -- kur avotu var apskatīt / pārbaudīt
  lejupielade   text,                 -- precīzs ieguves URL vai metode
  lietojums     text not null,        -- kam karte to izmanto
  piezime       text,
  kartiba       int not null default 100
);

insert into avoti (kods, nosaukums, izdevejs, licence, licences_url, atverts, datu_kopa_url, lejupielade, lietojums, piezime, kartiba) values
  ('vugd-112', 'Publiskās patvertnes (112.lv patvertņu karte)', 'VUGD / Iekšlietu ministrijas Informācijas centrs',
   'Licence nav norādīta', null, false, 'https://www.112.lv/lv/patvertnes',
   'https://services9.arcgis.com/f2QOaaoX08g1sAc2/arcgis/rest/services/PatvertnesDati_view/FeatureServer/0',
   'Patvertnes (781)',
   'Nav publicēts data.gov.lv; dati nolasīti no publiskā 112.lv ArcGIS kartes servisa (hakatona komplekts). Atvērta ir tikai Rīgas patvertņu kopa (Rīgas dome, CC BY 4.0).', 10),
  ('vm-24h', 'Slimnīcu saraksts, kurās 24 stundas diennaktī tiek nodrošināta neatliekamā medicīniskā palīdzība', 'Veselības ministrija',
   'Oficiāls dokuments, nav autortiesību objekts (Autortiesību likuma 6. pants)', 'https://likumi.lv/ta/id/5138-autortiesibu-likums', true,
   null, 'Valsts katastrofu medicīnas plāna 12. pielikums, apstiprināts ar VM 04.03.2026. rīkojumu Nr. 01-01.1/26 (PDF repozitorijā: ai-open-data-2026-hakatons/atseviski_dati/)',
   'Neatliekamā palīdzība 24/7 (37 slimnīcas): saraksts un nosaukumi',
   'Koordinātas un adreses no VZD adrešu reģistra; PSKUS un RAKUS uzņemšanas ieejas no OpenStreetMap. Oriģinālā publicēšanas saite vēl jānoskaidro.', 20),
  ('iemic-arstniecibas', 'VKCP IĢIS – ārstniecības iestāžu adreses', 'Iekšlietu ministrijas Informācijas centrs',
   'CC0 1.0', 'https://creativecommons.org/publicdomain/zero/1.0/', true,
   'https://data.gov.lv/dati/lv/dataset/vkcp-igis-arstniecibas-iestazu-adreses',
   'https://data.gov.lv/dati/dataset/05068340-d155-49cc-9a37-ab7d63ccd769/resource/5ea6e4aa-ee21-462a-8590-283483d2b0a4/download/medicinasiestades.csv',
   'Slimnīcas un ārstniecības iestādes', 'Bez ģimenes ārstu praksēm.', 30),
  ('zva-fdu', 'Farmaceitiskās darbības uzņēmumu reģistrs', 'Zāļu valsts aģentūra',
   'CC0 1.0', 'https://creativecommons.org/publicdomain/zero/1.0/', true,
   'https://data.gov.lv/dati/lv/dataset/farmaceitiskas-darbibas-uznemumu-registrs',
   'https://dati.zva.gov.lv/fdu-registrs/export/fdu_register.csv',
   'Aptiekas', 'Vispārēja tipa aptiekas un to filiāles ar spēkā esošu licenci un koordinātām.', 40),
  ('iemic-vp', 'VKCP IĢIS – VP iecirkņu adreses', 'Iekšlietu ministrijas Informācijas centrs',
   'CC0 1.0', 'https://creativecommons.org/publicdomain/zero/1.0/', true,
   'https://data.gov.lv/dati/lv/dataset/vkcp-igis-vp-iecirknu-adreses',
   'https://data.gov.lv/dati/dataset/f37fb118-4dfe-4011-9816-ebe964ebc203/resource/80cc2dd9-f424-4c5c-9bbc-a01c02bfcb28/download/vp_iecirknu_adreses.csv',
   'Policija (Valsts policija)', '8 iecirkņu nosaukumos avota failā bojāts kodējums (cp1257 kā latin-1); valsts_dati.py to izlabo.', 50),
  ('iemic-pp', 'VKCP IĢIS – Pašvaldības policijas vienību adreses', 'Iekšlietu ministrijas Informācijas centrs',
   'CC0 1.0', 'https://creativecommons.org/publicdomain/zero/1.0/', true,
   'https://data.gov.lv/dati/lv/dataset/vkcp-igis-pasvaldibas-policijas-vienibu-adreses',
   'https://data.gov.lv/dati/dataset/af093e35-5962-41d8-9f3f-f59312c5616f/resource/1a11bf3a-b79d-4999-bb8d-67065b55bb3a/download/pp.csv',
   'Policija (pašvaldību policija)', 'Kopā ir tikai daļa pašvaldību.', 51),
  ('iemic-vugd', 'VKCP IĢIS – VUGD depo adreses', 'Iekšlietu ministrijas Informācijas centrs',
   'CC0 1.0', 'https://creativecommons.org/publicdomain/zero/1.0/', true,
   'https://data.gov.lv/dati/lv/dataset/vkcp-igis-vugd-depo-adreses',
   'https://data.gov.lv/dati/dataset/2466e938-6eba-4016-8ff8-f7e3f2736249/resource/a91ff743-e064-41d4-b449-b29d713fc6fb/download/vugd_depo_adreses.csv',
   'Ugunsdzēsēji (VUGD daļas un posteņi)', null, 60),
  ('osm', 'OpenStreetMap', 'OpenStreetMap līdzstrādnieki',
   'ODbL 1.0', 'https://opendatacommons.org/licenses/odbl/1-0/', true,
   'https://www.openstreetmap.org/copyright', 'Overpass API (overpass-api.de), src/karte/db/osm_poi.py',
   'Bankomāti, degvielas uzpildes stacijas; 2 slimnīcu uzņemšanas ieejas', 'Valsts atvērto datu par bankomātiem un DUS nav.', 70),
  ('vzd-varis', 'Valsts adrešu reģistra informācijas sistēmas atvērtie dati', 'Valsts zemes dienests',
   'CC BY 4.0', 'https://creativecommons.org/licenses/by/4.0/', true,
   'https://data.gov.lv/dati/lv/dataset/varis-atvertie-dati', 'aw_shp.zip (robežas), aw_eka.csv (adrešu koordinātas)',
   'Novadu, valstspilsētu un pilsētu robežas; adrešu meklēšana; 24/7 slimnīcu adreses un koordinātas', null, 80),
  ('lvgmc-hidro', 'Hidrometeoroloģiskie novērojumi (hidroloģiskie operatīvie dati)', 'Latvijas Vides, ģeoloģijas un meteoroloģijas centrs',
   'CC0 1.0', 'https://creativecommons.org/publicdomain/zero/1.0/', true,
   'https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-noverojumi',
   'hidro_stacijas.csv + hidro_operativie_dati.csv (katru stundu, src/karte/db/udens_limenis.py)',
   'Ūdens līmenis un ūdens temperatūra hidroloģiskajās stacijās',
   'Līmenis cm virs posteņa nulles (m LAS-2000,5 = nulle + cm/100); laiks UTC. Bīstamības līmeņi (PRIS) nav atvērtie dati, tāpēc netiek rādīti. Mērījums vecāks par 6 h kartē netiek rādīts.', 75),
  ('lvgmc-bridinajumi', 'Hidrometeoroloģiskie brīdinājumi', 'Latvijas Vides, ģeoloģijas un meteoroloģijas centrs',
   'CC0 1.0', 'https://creativecommons.org/publicdomain/zero/1.0/', true,
   'https://data.gov.lv/dati/lv/dataset/hidrometeorologiskie-bridinajumi',
   'bridinajumu_metadata.csv + bridinajumu_poligoni.csv (karte_api.py /api/bridinajumi, kešs 10 min)',
   'Brīdinājumu josla lapas augšā; vai brīdinājums attiecas uz izvēlēto adresi', 'Laiks — Latvijas vietējais.', 76),
  ('lvgmc-pludi', '3. cikla Latvijas plūdu postījumu vietu un plūdu riska kartes (2026–2031)', 'Latvijas Vides, ģeoloģijas un meteoroloģijas centrs / ĢeoLatvija.lv',
   'CC0 1.0', 'https://creativecommons.org/publicdomain/zero/1.0/', true,
   'https://data.gov.lv/dati/lv/dataset/3-cikla-latvijas-pldu-postjumu-vietu-un-pldu-riska-kartes1',
   'WMS geo-dpps.viss.gov.lv (pavasara pali, ledus sastrēgumi, jūras vējuzplūdi; 10 %, 1 %, 0,5 %), GetFeatureInfo /api/pludi',
   'Plūdu riska zonu slānis kartē; vai adrese ir applūstošā teritorijā', 'Applūstošo teritoriju ārējās robežas; ūdens dziļuma klases ir maksas dati.', 77),
  ('osm-karte', 'OpenStreetMap karšu fons', 'OpenStreetMap Foundation',
   'ODbL 1.0 (dati), CC BY-SA 2.0 (attēli); flīžu lietošanas noteikumi', 'https://operations.osmfoundation.org/policies/tiles/', true,
   'https://www.openstreetmap.org/copyright', 'https://tile.openstreetmap.org',
   'Fona karte', 'Lietošanas noteikumi aizliedz intensīvu lietošanu un masveida lejupielādi.', 90)
on conflict (kods) do update set
  nosaukums = excluded.nosaukums, izdevejs = excluded.izdevejs, licence = excluded.licence,
  licences_url = excluded.licences_url, atverts = excluded.atverts, datu_kopa_url = excluded.datu_kopa_url,
  lejupielade = excluded.lejupielade, lietojums = excluded.lietojums, piezime = excluded.piezime, kartiba = excluded.kartiba;

-- Visi punkti kartē. Katrs avots (avots) tiek ielādēts un aizvietots kā vesels (ielade.py).
-- Incidentiem aizpilda derigs_no/derigs_lidz; API rāda tikai vēl spēkā esošos.
create table if not exists objekti (
  id             bigserial primary key,
  kategorija     text not null references kategorijas (kods) on update cascade,
  nosaukums      text,
  adrese         text,
  ipasibas       jsonb not null default '{}',
  avots          text not null,
  avota_id       text not null,
  derigs_no      timestamptz,
  derigs_lidz    timestamptz,
  geom           geometry(Point, 4326) not null,
  pasvaldiba_kods text,                         -- novads vai valstspilsēta (aizpilda trigeris)
  pilseta_kods   text,                          -- pilsēta, ja punkts ir tajā
  atjaunots      timestamptz not null default now(),
  unique (avots, avota_id)
);
create index if not exists objekti_geom_idx on objekti using gist (geom);
create index if not exists objekti_kategorija_idx on objekti (kategorija);
create index if not exists objekti_pasvaldiba_idx on objekti (pasvaldiba_kods);
create index if not exists objekti_pilseta_idx on objekti (pilseta_kods);

create or replace function objekti_piesaistit_regionam() returns trigger language plpgsql as $$
begin
  select kods into new.pasvaldiba_kods from regioni
   where tips in ('novads', 'valstspilseta') and st_intersects(geom, new.geom) limit 1;
  select kods into new.pilseta_kods from regioni
   where tips in ('pilseta', 'valstspilseta') and st_intersects(geom, new.geom) limit 1;
  return new;
end $$;

drop trigger if exists objekti_regions on objekti;
create trigger objekti_regions before insert or update of geom on objekti
  for each row execute function objekti_piesaistit_regionam();

-- Katram objektam obligāti norādīts avots no tabulas avoti.
do $$ begin
  alter table objekti add constraint objekti_avots_fk foreign key (avots) references avoti (kods) on update cascade;
exception when duplicate_object then null;
end $$;

-- Adrešu meklēšana: ēku adreses ar koordinātām (VZD adrešu reģistrs, aw_eka.csv; ielāde: adreses.sh).
-- meklesanai = adrese mazajiem burtiem bez garumzīmēm; trigrammu indekss ļauj meklēt pēc vārdu daļām.
create extension if not exists pg_trgm;
create extension if not exists unaccent;
create table if not exists adreses (
  kods       text primary key,                  -- VZD adrešu reģistra kods
  adrese     text not null,                     -- pilnā adrese (STD), piem. "Brīvības iela 15, Ogre, Ogres nov., LV-5001"
  meklesanai text not null,
  geom       geometry(Point, 4326) not null
);
create index if not exists adreses_meklesanai_idx on adreses using gin (meklesanai gin_trgm_ops);

-- Publiskais API lieto map_api: tikai lasīšana.
grant usage on schema public to map_api;
grant select on regioni, kategorijas, objekti, avoti, adreses to map_api;

-- Pašvaldību CA plānu slāņi (src/karte/db/ca_plani.py). Katram punktam ipasibas satur plāna lappusi
-- (lpp), saiti (plans_url), gatavu atsauces tekstu (avots_teksts) un pārbaudes karodziņus (karodzini).
insert into kategorijas (kods, nosaukums, grupa, krasa, kartiba) values
  ('evakuacijas_punkts', 'Evakuācijas pulcēšanās vietas (pašvaldību CA plāni)', 'patvertnes', '#0f766e', 11),
  ('izmitinasana', 'Pagaidu izmitināšanas vietas (pašvaldību CA plāni)', 'patvertnes', '#0369a1', 12)
on conflict (kods) do update set
  nosaukums = excluded.nosaukums, grupa = excluded.grupa, krasa = excluded.krasa, kartiba = excluded.kartiba;

insert into avoti (kods, nosaukums, izdevejs, licence, licences_url, atverts, datu_kopa_url, lejupielade, lietojums, piezime, kartiba) values
  ('ca-plani', 'Pašvaldību civilās aizsardzības plāni', 'Katra pašvaldība (izdevējs un plāna saite norādīti katram punktam)',
   'Oficiāls dokuments, nav autortiesību objekts (Autortiesību likuma 6. pants)', 'https://likumi.lv/ta/id/5138-autortiesibu-likums', true,
   'https://github.com/lata-org/ai-open-data-2026-hakatons/tree/main/ca-plani-hakatons',
   'Plānu PDF/DOCX no pašvaldību tīmekļvietnēm (ipasibas.plans_url), pārveidoti Markdown; vietas izvilktas ar AI + regex, katra pārbaudīta pret plāna tekstu (src/karte/db/ca_plani.py)',
   'Evakuācijas pulcēšanās vietas; pagaidu izmitināšanas vietas',
   'Koordinātas no plāna; ja plānā tikai adrese vai koordinātas ir kļūdainas, tās ģeokodētas ar VZD adrešu reģistru. Kvalitāte: notes/ca-plani-kvalitate.md.', 15)
on conflict (kods) do update set
  nosaukums = excluded.nosaukums, izdevejs = excluded.izdevejs, licence = excluded.licence,
  licences_url = excluded.licences_url, atverts = excluded.atverts, datu_kopa_url = excluded.datu_kopa_url,
  lejupielade = excluded.lejupielade, lietojums = excluded.lietojums, piezime = excluded.piezime, kartiba = excluded.kartiba;

-- ---- Biežāk meklētais (meklesana.js → POST /api/meklejumi; GET /api/meklejumi/top) ----
-- Tikai normalizēts vaicājuma teksts un skaitītāji: bez IP, laika pa lietotājiem vai citiem lietotāja datiem.
-- Vaicājumus ar cipariem (mājas numuri = adreses) API neskaita; klienti sūta vaicājumu bez adreses.
create table if not exists meklejumi (
  id         bigserial primary key,
  vaicajums  text not null unique check (length(vaicajums) between 1 and 100),  -- mazie burti, viena atstarpe
  skaits     int  not null default 1,            -- cik reižu meklēts ar atpazītu situāciju vai slāni
  klikski    int  not null default 0,            -- cik reižu pēc tā atvērts rezultāts
  pedejais   timestamptz not null default now()
);
create index if not exists meklejumi_pedejais_idx on meklejumi (pedejais);
grant select, insert, update on meklejumi to map_api;
grant usage on sequence meklejumi_id_seq to map_api;

-- Demo: lai "Biežāk meklētais" nekad nav tukšs
insert into meklejumi (vaicajums, skaits) values
  ('nav elektrības', 12), ('plūdi ogrē', 9), ('tuvākā patvertne', 7), ('nav ūdens', 5), ('evakuācija', 4)
on conflict (vaicajums) do nothing;

-- ==== Statuss (production/statuss.html) ====
-- Fona pārbaužu rezultāti: karte_api.py ik 15 min ieraksta vienu rindu par katru komponentu (vietne, API, datu avoti),
-- glabā 8 dienas. Tabulu izveido arī pats API (tas pats bloks STATUSS_SHEMA failā karte_api.py), ja shēma nav palaista.
create table if not exists statuss_parbaudes (
  id         bigserial primary key,
  komponents text not null,
  laiks      timestamptz not null default now(),
  stavoklis  text not null check (stavoklis in ('darbojas', 'traucejumi', 'nedarbojas')),
  zinojums   text,
  ilgums_ms  int
);
create index if not exists statuss_parbaudes_laiks_idx on statuss_parbaudes (laiks);
grant select on statuss_parbaudes to map_api;
