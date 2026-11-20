"""Ingestão Bronze: Data Dragon -> Supabase (bronze.ddragon_raw).

Baixa o catálogo estático (campeões, itens, runas) da versão mais recente
e grava o JSON bruto. Idempotente: se o par (recurso, versão) já existe,
não baixa de novo. Uma nova linha só entra quando sai um patch novo.

Uso:
    python ingestion/ingest_ddragon.py
"""
import os

import psycopg2
import requests
from dotenv import load_dotenv
from psycopg2.extras import Json

load_dotenv(override=True, encoding="utf-8-sig")

BASE_URL = "https://ddragon.leagueoflegends.com"
LOCALE = os.getenv("DDRAGON_LOCALE", "pt_BR")
RESOURCES = ["champion", "item", "runesReforged"]


def latest_version():
    resp = requests.get(f"{BASE_URL}/api/versions.json", timeout=30)
    resp.raise_for_status()
    return resp.json()[0]


def fetch_resource(version, resource):
    url = f"{BASE_URL}/cdn/{version}/data/{LOCALE}/{resource}.json"
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return resp.json()


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
    version = latest_version()
    print(f"Versão mais recente do Data Dragon: {version}")

    conn = connect_db()
    try:
        for resource in RESOURCES:
            with conn.cursor() as cur:
                cur.execute(
                    "select 1 from bronze.ddragon_raw where resource = %s and version = %s",
                    (resource, version),
                )
                if cur.fetchone():
                    print(f"  {resource}: já na Bronze, pulando")
                    continue

            payload = fetch_resource(version, resource)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into bronze.ddragon_raw (resource, version, payload)
                    values (%s, %s, %s)
                    on conflict (resource, version) do nothing
                    """,
                    (resource, version, Json(payload)),
                )
            conn.commit()
            print(f"  {resource}: gravado")
    finally:
        conn.close()

    print("Ingestão do Data Dragon concluída.")


if __name__ == "__main__":
    main()