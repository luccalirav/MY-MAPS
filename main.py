#!/usr/bin/env python3
"""Mapa de bloqueio de notificação (raio de 150 m).

  python main.py                      gera mapas (pergunta endereço e coordenadas)
  python main.py kml ARQUIVO.kml      atualiza o KML e registra a data
  python main.py status               mostra qual KML está em uso e quando foi atualizado
"""
import argparse
import sys
from pathlib import Path

from mapas import config, desenho, entrada, kml


def _mostrar_status() -> bool:
    info = kml.ler_info()
    if not info or not kml.caminho_kml_atual():
        print('Nenhum KML registrado ainda.')
        print('Registre um com:  python main.py kml "C:\\caminho\\arquivo.kml"')
        return False
    print(f"KML em uso     : {info['nome_original']}")
    print(f"Atualizado em  : {kml.formatar_data(info['atualizado_em'])}")
    print(f"Quarteirões    : {info['quarteiroes']}   Localidades: {info['localidades']}")
    return True


def cmd_kml(args) -> int:
    try:
        info = kml.importar_kml(args.arquivo)
    except kml.ErroKML as e:
        print(f'✗ {e}')
        return 1
    print(f"✓ KML atualizado em {kml.formatar_data(info['atualizado_em'])}")
    print(f"  Arquivo: {info['nome_original']}")
    print(f"  Quarteirões: {info['quarteiroes']}   Localidades: {info['localidades']}")
    antes = info.get('quarteiroes_antes')
    if antes is not None:
        print(f'  Antes: {antes} quarteirões (diferença: {info["quarteiroes"] - antes:+d})')
    return 0


def cmd_status(args) -> int:
    return 0 if _mostrar_status() else 1


def cmd_gerar(args) -> int:
    if not _mostrar_status():
        return 1
    mapa = kml.carregar_kml(kml.caminho_kml_atual())
    pasta = Path(args.saida)
    pasta.mkdir(parents=True, exist_ok=True)

    def gerar(endereco, lat, lon):
        destino = pasta / entrada.nome_arquivo(endereco)
        resultado = desenho.gerar_pdf(mapa, endereco, lat, lon, destino)
        return destino, resultado.avisos

    entrada.fluxo_interativo(gerar, pasta)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description='Mapa de bloqueio de notificação (raio de 150 m)')
    ap.add_argument('--saida', default=str(config.PASTA_SAIDA), help='pasta onde os PDFs são salvos')
    sub = ap.add_subparsers(dest='comando')
    p = sub.add_parser('kml', help='atualiza o KML e registra a data')
    p.add_argument('arquivo')
    sub.add_parser('status', help='mostra o KML em uso e a data da última atualização')
    args = ap.parse_args(argv)
    return {'kml': cmd_kml, 'status': cmd_status}.get(args.comando, cmd_gerar)(args)


if __name__ == '__main__':
    sys.exit(main())
