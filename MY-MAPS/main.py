#!/usr/bin/env python3
"""Mapa de bloqueio de notificação (raio de 150 m).

  python main.py          gera mapas (pergunta endereço e coordenadas)
  python main.py status   mostra qual KML está em uso

O KML usado é sempre o arquivo mais recente da pasta de KML.
Para trocar a base: coloque o KML novo na pasta e apague o mais antigo.
"""
import argparse
import sys
from pathlib import Path

from mapas import config, desenho, entrada, kml


def _info(fonte: kml.FonteKML) -> str:
    arq = fonte.arquivo()
    return f'{arq.nome} (arquivo de {arq.data_formatada})'


def _mostrar_status(fonte: kml.FonteKML) -> bool:
    try:
        print(f'Pasta do KML : {fonte.pasta}')
        print(f'KML em uso   : {_info(fonte)}')
        for aviso in fonte.avisos():
            print(f'  ⚠ {aviso}')
        return True
    except kml.ErroKML as e:
        print(f'✗ {e}')
        return False


def cmd_status(args) -> int:
    return 0 if _mostrar_status(kml.FonteKML(config.pasta_kml(args.pasta_kml))) else 1


def cmd_gerar(args) -> int:
    fonte = kml.FonteKML(config.pasta_kml(args.pasta_kml))
    if not _mostrar_status(fonte):
        return 1
    try:
        fonte.carregar()                                   # falha cedo se o KML estiver ilegível
    except kml.ErroKML as e:
        print(f'✗ {e}')
        return 1
    pasta = Path(args.saida)
    pasta.mkdir(parents=True, exist_ok=True)

    def gerar(endereco, lat, lon):
        mapa, _ = fonte.carregar()                         # sempre o KML mais recente da pasta
        destino = pasta / entrada.nome_arquivo(endereco)
        resultado = desenho.gerar_pdf(mapa, endereco, lat, lon, destino)
        return destino, resultado.avisos

    entrada.fluxo_interativo(gerar, pasta, info_kml=lambda: _info(fonte))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description='Mapa de bloqueio de notificação (raio de 150 m)')
    ap.add_argument('--saida', default=str(config.PASTA_SAIDA), help='pasta onde os PDFs são salvos')
    ap.add_argument('--pasta-kml', default=None, help='pasta onde ficam os KML (padrão: config.py)')
    sub = ap.add_subparsers(dest='comando')
    sub.add_parser('status', help='mostra o KML em uso')
    args = ap.parse_args(argv)
    return {'status': cmd_status}.get(args.comando, cmd_gerar)(args)


if __name__ == '__main__':
    sys.exit(main())
