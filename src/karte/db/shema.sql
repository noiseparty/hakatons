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
  ('bankomats',  'Bankomāti',                'infrastruktura', '#1d4ed8', 20),
  ('aptieka',    'Aptiekas',                 'infrastruktura', '#15803d', 30),
  ('slimnica',   'Slimnīcas',                'infrastruktura', '#be185d', 40),
  ('policija',   'Policija',                 'infrastruktura', '#1e3a8a', 50),
  ('ugunsdzeseji', 'Ugunsdzēsēji (VUGD)',    'infrastruktura', '#c2410c', 60),
  ('degviela',   'Degvielas uzpildes stacijas', 'infrastruktura', '#a16207', 70)
on conflict (kods) do update set
  nosaukums = excluded.nosaukums, grupa = excluded.grupa, krasa = excluded.krasa, kartiba = excluded.kartiba;

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

-- Publiskais API lieto map_api: tikai lasīšana.
grant usage on schema public to map_api;
grant select on regioni, kategorijas, objekti to map_api;
