with latest as (
    select version, payload
    from {{ source('bronze', 'ddragon_raw') }}
    where resource = 'champion'
    order by ingested_at desc
    limit 1
)

select
    (c.champion->>'key')::int   as champion_id,
    c.champion->>'id'           as champion_slug,
    c.champion->>'name'         as champion_name,
    c.champion->>'title'        as champion_title,
    c.champion->'tags'->>0      as primary_role,
    l.version                   as ddragon_version
from latest as l
cross join lateral jsonb_each(l.payload->'data') as c(champion_key, champion)