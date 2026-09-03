import argparse

from custos_precificacao.custeio import executar_custeio
from custos_precificacao.db import SessionLocal
from custos_precificacao.models import CusteioProduto, Produto


def custeio_run(observacao: str | None) -> None:
    with SessionLocal() as session:
        execucao = executar_custeio(session, observacao=observacao)
        produtos = {p.id: p for p in session.query(Produto).all()}
        resultados = (
            session.query(CusteioProduto).filter(CusteioProduto.execucao_id == execucao.id).all()
        )

        print(f"Execução #{execucao.id} em {execucao.executado_em}")
        for r in resultados:
            produto = produtos[r.produto_id]
            print(
                f"  {produto.codigo:10s} {produto.nome:40.40s} "
                f"maquina={r.custo_maquina:.4f} ambiente={r.custo_ambiente:.4f} "
                f"mao_de_obra={r.custo_mao_de_obra:.4f} insumos={r.custo_insumos:.4f} "
                f"-> total_unitario={r.custo_total_unitario:.4f}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(prog="custos_precificacao")
    subparsers = parser.add_subparsers(dest="comando", required=True)

    custeio_parser = subparsers.add_parser("custeio-run", help="Executa uma rodada de custeio")
    custeio_parser.add_argument("--observacao", default=None)

    args = parser.parse_args()

    if args.comando == "custeio-run":
        custeio_run(args.observacao)


if __name__ == "__main__":
    main()
