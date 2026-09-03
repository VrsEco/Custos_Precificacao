from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from custos_precificacao.models import CusteioExecucao, CusteioProduto, Produto


@dataclass
class CustoProduto:
    custo_maquina: Decimal
    custo_ambiente: Decimal
    custo_mao_de_obra: Decimal
    custo_insumos: Decimal

    @property
    def custo_lote_total(self) -> Decimal:
        return self.custo_maquina + self.custo_ambiente + self.custo_mao_de_obra + self.custo_insumos

    def custo_unitario(self, produto: Produto) -> Decimal:
        rendimento = produto.rendimento_un or produto.rendimento_kg
        if not rendimento:
            return self.custo_lote_total
        return self.custo_lote_total / rendimento


def _custo_insumo_produto_por_kg(session: Session, produto: Produto, _visitados: set[int]) -> Decimal:
    """Custo por kg de um produto/semiacabado quando consumido como insumo de outro produto."""
    if produto.id in _visitados:
        raise RuntimeError(f"Ciclo detectado no roteiro do produto {produto.codigo!r}")
    if not produto.rendimento_kg:
        raise ValueError(f"Produto {produto.codigo!r} não tem rendimento_kg definido, não pode ser usado como insumo por kg")

    custo = calcular_custo_produto(session, produto, _visitados | {produto.id})
    return custo.custo_lote_total / produto.rendimento_kg


def calcular_custo_produto(session: Session, produto: Produto, _visitados: set[int] | None = None) -> CustoProduto:
    """Calcula o custo do lote/receita de um produto a partir do seu roteiro.

    Resolve semiacabados usados como insumo (roteiro_insumo.insumo_produto) recursivamente.
    """
    visitados = (_visitados or set()) | {produto.id}

    custo_maquina = sum(
        (linha.tempo_horas * linha.maquina.custo_hora for linha in produto.roteiro_maquina),
        Decimal(0),
    )
    custo_ambiente = sum(
        (linha.tempo_horas * linha.ambiente.custo_hora for linha in produto.roteiro_ambiente),
        Decimal(0),
    )
    custo_mao_de_obra = sum(
        (linha.tempo_horas * linha.funcionario.custo_hora for linha in produto.roteiro_mao_de_obra),
        Decimal(0),
    )

    custo_insumos = Decimal(0)
    for linha in produto.roteiro_insumo:
        if linha.insumo_id is not None:
            custo_unitario = linha.insumo.custo_final
        else:
            custo_unitario = _custo_insumo_produto_por_kg(session, linha.insumo_produto, visitados)
        custo_insumos += linha.quantidade_kg * custo_unitario

    return CustoProduto(
        custo_maquina=custo_maquina,
        custo_ambiente=custo_ambiente,
        custo_mao_de_obra=custo_mao_de_obra,
        custo_insumos=custo_insumos,
    )


def executar_custeio(session: Session, observacao: str | None = None) -> CusteioExecucao:
    """Calcula o custo de todos os produtos e grava uma nova rodada de custeio."""
    execucao = CusteioExecucao(observacao=observacao)
    session.add(execucao)
    session.flush()

    for produto in session.query(Produto).all():
        custo = calcular_custo_produto(session, produto)
        session.add(
            CusteioProduto(
                execucao_id=execucao.id,
                produto_id=produto.id,
                custo_maquina=custo.custo_maquina,
                custo_ambiente=custo.custo_ambiente,
                custo_mao_de_obra=custo.custo_mao_de_obra,
                custo_insumos=custo.custo_insumos,
                custo_total_unitario=custo.custo_unitario(produto),
            )
        )

    session.commit()
    return execucao
