select
    item_id,
    item_name,
    item_plaintext,
    gold_base,
    gold_total,
    is_purchasable,
    'https://ddragon.leagueoflegends.com/cdn/' || ddragon_version
        || '/img/item/' || item_id || '.png' as icon_url
from {{ ref('stg_item') }}

union all

select 0, 'Sem item', null, 0, 0, false, null