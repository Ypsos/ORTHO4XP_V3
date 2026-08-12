# ============================================================
# Copyright (c) 2024-2026 Roland (Ypsos)
#
# CRÉDIT — AUTEUR : Roland (Ypsos) — Mars 2026
# Module conçu et spécifié par Roland (Ypsos) pour Ortho4XP V3.
# Cette notice d'auteur et de copyright doit être conservée
# conformément à la GPLv3.
# ============================================================
# Copyright (c) 2024-2026 Roland (Ypsos)
#
# CREDIT — AUTHOR: Roland (Ypsos) — March 2026
# Module designed and specified by Roland (Ypsos) for Ortho4XP V3.
# This authorship and copyright notice must be retained
# in accordance with GPLv3.
# ============================================================
# -*- coding: utf-8 -*-
"""
O4_HTTP_Client.py
Client HTTP moderne (httpx + asyncio) - module additif
Compatible Linux / macOS / Windows
N'altère aucun fichier existant.
"""

from __future__ import annotations

import asyncio
import sys
from typing import Optional, Dict, List

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    httpx = None


def _parse_retry_after(value: Optional[str]) -> Optional[float]:
    """
    Interprète l'en-tête HTTP 'Retry-After'.
    Deux formats possibles selon la norme HTTP :
      - un nombre de secondes (ex. "120")
      - une date HTTP absolue (ex. "Wed, 21 Oct 2026 07:28:00 GMT")
    Retourne un délai en secondes (float) ou None si non interprétable.
    """
    if not value:
        return None
    value = value.strip()
    # Cas 1 : délai en secondes
    try:
        return max(0.0, float(value))
    except (ValueError, TypeError):
        pass
    # Cas 2 : date HTTP absolue
    try:
        from email.utils import parsedate_to_datetime
        import datetime
        dt = parsedate_to_datetime(value)
        if dt is None:
            return None
        now = datetime.datetime.now(dt.tzinfo)
        delay = (dt - now).total_seconds()
        return max(0.0, delay)
    except Exception:
        return None


class HTTPClient:
    """
    Client HTTP asynchrone basé sur httpx.
    Fallback silencieux si httpx n'est pas installé.
    """

    def __init__(
        self,
        timeout: float = 30.0,
        max_connections: int = 20,
        retries: int = 3,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.timeout = timeout
        self.max_connections = max_connections
        self.retries = retries
        self.headers = headers or {
            "User-Agent": "Ortho4XP/3.0 (compatible; modern-http-client)"
        }
        self._client = None

    async def _get_client(self):
        if not HAS_HTTPX:
            raise RuntimeError(
                "httpx n'est pas installé. "
                "Installez-le avec : pip install httpx"
            )
        if self._client is None:
            limits = httpx.Limits(
                max_connections=self.max_connections,
                max_keepalive_connections=10,
            )
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                limits=limits,
                headers=self.headers,
                follow_redirects=True,
            )
        return self._client

    async def get_bytes(self, url: str, headers: Optional[Dict[str, str]] = None) -> bytes:
        client = await self._get_client()
        last_error = None

        for attempt in range(1, self.retries + 1):
            try:
                resp = await client.get(url, headers=headers)
                # Gestion spécifique HTTP 429 (Too Many Requests) :
                # on lit l'en-tête Retry-After et on respecte le délai demandé
                # par le serveur. Si absent, on retombe sur le backoff habituel.
                if getattr(resp, "status_code", None) == 429:
                    if attempt < self.retries:
                        retry_after = _parse_retry_after(
                            resp.headers.get("Retry-After")
                        )
                        if retry_after is not None:
                            wait = retry_after
                        else:
                            wait = 1.0 * attempt
                        last_error = RuntimeError("HTTP 429 Too Many Requests")
                        await asyncio.sleep(wait)
                        continue
                    else:
                        resp.raise_for_status()
                resp.raise_for_status()
                return resp.content
            except Exception as e:
                last_error = e
                if attempt < self.retries:
                    await asyncio.sleep(1.0 * attempt)

        raise RuntimeError(f"Échec après {self.retries} tentatives : {url} → {last_error}")

    async def get_many(self, urls: List[str], headers: Optional[Dict[str, str]] = None) -> List[Optional[bytes]]:
        async def _one(url: str) -> Optional[bytes]:
            try:
                return await self.get_bytes(url, headers=headers)
            except Exception:
                return None

        tasks = [_one(u) for u in urls]
        return await asyncio.gather(*tasks)

    async def close(self):
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def get_bytes_sync(self, url: str, headers: Optional[Dict[str, str]] = None) -> bytes:
        return asyncio.run(self.get_bytes(url, headers=headers))

    def get_many_sync(self, urls: List[str], headers: Optional[Dict[str, str]] = None) -> List[Optional[bytes]]:
        return asyncio.run(self.get_many(urls, headers=headers))


def download(url: str, timeout: float = 30.0) -> bytes:
    client = HTTPClient(timeout=timeout)
    return client.get_bytes_sync(url)


def download_many(urls: List[str], timeout: float = 30.0) -> List[Optional[bytes]]:
    client = HTTPClient(timeout=timeout)
    return client.get_many_sync(urls)


if __name__ == "__main__":
    print("O4_HTTP_Client — test rapide")
    print(f"httpx disponible : {HAS_HTTPX}")

    if not HAS_HTTPX:
        print("→ Installez httpx : pip install httpx")
        sys.exit(1)

    test_url = "https://httpbin.org/bytes/64"
    try:
        data = download(test_url)
        print(f"Téléchargement OK — {len(data)} octets reçus")
    except Exception as e:
        print(f"Erreur : {e}")
