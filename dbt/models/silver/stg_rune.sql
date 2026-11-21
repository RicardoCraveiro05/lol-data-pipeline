with latest as (
    select version, payload
    from {{ source('bronze', 'ddragon_raw') }}
    where resource = 'runesReforged'
    order by ingested_at desc
    limit 1
)

select
    (r.rune->>'id')::int      as rune_id,
    r.rune->>'key'            as rune_key,
    r.rune->>'name'           as rune_name,
    r.rune->>'icon'           as rune_icon,
    (s.style->>'id')::int     as style_id,
    s.style->>'name'          as style_name,
    (sl.slot_number - 1)      as slot_index,
    l.version                 as ddragon_version
from latest as l
cross join lateral jsonb_array_elements(l.payload) as s(style)
cross join lateral jsonb_array_elements(s.style->'slots') with ordinality as sl(slot, slot_number)
cross join lateral jsonb_array_elements(sl.slot->'runes') as r(rune)