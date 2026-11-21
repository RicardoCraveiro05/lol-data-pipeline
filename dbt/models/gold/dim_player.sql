select distinct on (p.puuid)
    p.puuid,
    p.riot_id_name,
    p.riot_id_tag,
    m.game_start_ts as last_seen_ts
from {{ ref('stg_participant') }} as p
join {{ ref('stg_match') }} as m using (match_id)
order by p.puuid, m.game_start_ts desc