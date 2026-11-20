"""Ingestão Bronze: Riot API -> Supabase (bronze.matches_raw).

Para cada Riot ID acompanhado:
  1. resolve o puuid (account-v1)
  2. lista os últimos match_ids (match-v5)
  3. baixa o JSON das partidas que ainda não estão na Bronze
  4. grava o JSON bruto, sem tratamento

Idempotente: rodar várias vezes não duplica partidas.

Uso:
    python ingestion/ingest_matches.py
"""
import os
import sys
import time
from urllib.parse import quote

import psycopg2
import requests
from dotenv import load_dotenv
from psycopg2.extras import Json

load_dotenv(override=True)

RIOT_API_KEY = os.environ["RIOT_API_KEY"].strip()
RIOT_REGION = os.getenv("RIOT_REGION", "americas")  # BR usa "americas"
TRACKED_RIOT_IDS = [
    x.strip() for x in os.environ["TRACKED_RIOT_IDS"].split(",") if x.strip()
]  # formato: "Nome#TAG,Outro#TAG"
MATCH_COUNT = int(os.getenv("MATCH_COUNT", "20"))
# Chave de desenvolvimento: 100 requisições a cada 2 min (~1,2s por chamada)
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "1.25"))

BASE_URL = f"https://{RIOT_REGION}.api.riotgames.com"
HEADERS = {"X-Riot-Token": RIOT_API_KEY}


def riot_get(path, params=None):
    """GET na Riot API com tratamento de rate limit (429) e erros 5xx."""
    url = f"{BASE_URL}{path}"
    for attempt in range(5):
        resp = requests.get(url, headers=HEADERS, params=params, timeout=30)
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", 10)) + 1
            print(f"  limite de requisições atingido, aguardando {wait}s")
            time.sleep(wait)
            continue
        if resp.status_code >= 500:
            time.sleep(2**attempt)
            continue
        resp.raise_for_status()
        time.sleep(REQUEST_DELAY)
        return resp.json()
    raise RuntimeError(f"Falha após 5 tentativas: {path}")


def get_puuid(riot_id):
    name, tag = riot_id.rsplit("#", 1)
    data = riot_get(
        f"/riot/account/v1/accounts/by-riot-id/{quote(name)}/{quote(tag)}"
    )
    return data["puuid"]


def get_match_ids(puuid):
    return riot_get(
        f"/lol/match/v5/matches/by-puuid/{puuid}/ids",
        params={"start": 0, "count": MATCH_COUNT},
    )


def connect_db():
    return psycopg2.connect(
        host=os.environ["SUPABASE_DB_HOST"],
        port=os.environ["SUPABASE_DB_PORT"],
        user=os.environ["SUPABASE_DB_USER"],
        password=os.environ["SUPABASE_DB_PASSWORD"],
        dbname=os.environ["SUPABASE_DB_NAME"],
        sslmode="require",
    )


def main():
    match_ids = set()
    for riot_id in TRACKED_RIOT_IDS:
        puuid = get_puuid(riot_id)
        ids = get_match_ids(puuid)
        print(f"{riot_id}: {len(ids)} partidas listadas")
        match_ids.update(ids)

    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "select match_id from bronze.matches_raw where match_id = any(%s)",
                (list(match_ids),),
            )
            existing = {row[0] for row in cur.fetchall()}

        new_ids = sorted(match_ids - existing)
        print(f"{len(match_ids)} únicas, {len(existing)} já na Bronze, {len(new_ids)} novas")

        for i, match_id in enumerate(new_ids, start=1):
            payload = riot_get(f"/lol/match/v5/matches/{match_id}")
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into bronze.matches_raw (match_id, payload)
                    values (%s, %s)
                    on conflict (match_id) do nothing
                    """,
                    (match_id, Json(payload)),
                )
            conn.commit()
            print(f"  [{i}/{len(new_ids)}] {match_id} gravada")
    finally:
        conn.close()

    print("Ingestão concluída.")


if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as err:
        print("Endereço chamado:", err.request.url)
        print("Status:", err.response.status_code)
        print("Resposta da Riot:", err.response.text[:300])
        raise SystemExit(1)