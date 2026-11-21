select
    rune_id,
    rune_key,
    rune_name,
    style_id,
    style_name,
    slot_index,
    slot_index = 0 as is_keystone,
    'https://ddragon.leagueoflegends.com/cdn/img/' || rune_icon as icon_url
from {{ ref('stg_rune') }}