"""
Global Education Data MCP Server
=================================
MCP-Server für internationalen Bildungsvergleich.
Entwickelt vom Schulamt der Stadt Zürich.

Quellen:
  - UNESCO Institute for Statistics (UIS): 4'000+ Bildungsindikatoren
  - OECD Education at a Glance: SDMX REST API, 38 OECD-Länder
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _distribution_version

try:
    # Aus den installierten Paket-Metadaten, die aus pyproject.toml erzeugt
    # werden. Ein von Hand gepflegtes Literal laeuft frueher oder spaeter
    # von der Paketversion weg — genau das ist portfolioweit passiert.
    __version__ = _distribution_version("global-education-mcp")
except PackageNotFoundError:
    # Quellbaum ohne Installation. Bewusst keine plausibel aussehende Nummer:
    # ein erkennbar unfertiger Marker ist besser als eine falsche Version.
    __version__ = "0.0.0+source"
__author__ = "Schulamt der Stadt Zürich"
