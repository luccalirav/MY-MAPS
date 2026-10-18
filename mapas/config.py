"""Constantes e caminhos do projeto."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA_DADOS = RAIZ / 'dados'          # KML atual e registro de atualização (fora do Git)
PASTA_SAIDA = RAIZ / 'saida'          # PDFs gerados (fora do Git)

KML_ATUAL = 'kml_atual.kml'
KML_ANTERIOR = 'kml_anterior.kml'
INFO_KML = 'kml_info.json'

RAIO_M = 150.0                        # raio do bloqueio
MARGEM_M = 190.0                      # meia altura da janela do mapa (raio + 40 m)
M_POR_GRAU_LAT = 110574.0             # convenção usada no modelo
M_POR_GRAU_LON_EQUADOR = 111320.0     # multiplicado por cos(latitude)
