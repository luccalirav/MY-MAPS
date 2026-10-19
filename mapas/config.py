"""Constantes e caminhos do projeto."""
import json
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA_SAIDA = RAIZ / 'saida'          # PDFs gerados (fora do Git)
ARQUIVO_LOCAL = RAIZ / 'config_local.json'   # ajustes só deste PC (fora do Git)

# Pasta onde ficam os KML. O programa usa sempre o arquivo mais recente que estiver nela.
PASTA_KML_PADRAO = RAIZ / 'KML'

RAIO_M = 150.0                        # raio do bloqueio
MARGEM_M = 190.0                      # meia altura da janela do mapa (raio + 40 m)
M_POR_GRAU_LAT = 110574.0             # convenção usada no modelo
M_POR_GRAU_LON_EQUADOR = 111320.0     # multiplicado por cos(latitude)


def pasta_kml(escolhida: str | None = None) -> Path:
    """Ordem: --pasta-kml  >  config_local.json ({"pasta_kml": "..."})  >  padrão."""
    if escolhida:
        return Path(escolhida)
    try:
        dados = json.loads(ARQUIVO_LOCAL.read_text(encoding='utf-8'))
        if dados.get('pasta_kml'):
            return Path(dados['pasta_kml'])
    except (OSError, ValueError):
        pass
    return PASTA_KML_PADRAO
