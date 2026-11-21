select
    champion_id,
    champion_slug,
    champion_name,
    champion_title,
    primary_role,
    'https://ddragon.leagueoflegends.com/cdn/' || ddragon_version
        || '/img/champion/' || champion_slug || '.png' as icon_url
from {{ ref('stg_champion') }}