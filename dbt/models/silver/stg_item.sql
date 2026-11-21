with latest as (
    select version, payload
    from {{ source('bronze', 'ddragon_raw') }}
    where resource = 'item'
    order by ingested_at desc
    limit 1
)

select
    i.item_key::int                            as item_id,
    i.item->>'name'                            as item_name,
    i.item->>'plaintext'                       as item_plaintext,
    (i.item->'gold'->>'base')::int             as gold_base,
    (i.item->'gold'->>'total')::int            as gold_total,
    (i.item->'gold'->>'purchasable')::boolean  as is_purchasable,
    l.version                                  as ddragon_version
from latest as l
cross join lateral jsonb_each(l.payload->'data') as i(item_key, item)