from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from custos_precificacao.custeio import calcular_custo_produto
from custos_precificacao.models import (
    Ambiente,
    Base,
    Funcionario,
    Insumo,
    Maquina,
    Processo,
    Produto,
    RoteiroAmbiente,
    RoteiroInsumo,
    RoteiroMaoDeObra,
    RoteiroMaquina,
    Setor,
)


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def _setup_recursos(session):
    setor = Setor(codigo="Set_01", nome="Granola")
    session.add(setor)
    session.flush()

    processo = Processo(codigo="Proce_01", setor_id=setor.id, nome="Mistura")
    ambiente = Ambiente(codigo="Inst_01", nome="Granola", valor_rateado_mensal=Decimal("1000"), horas_uteis_mensais=Decimal("100"))
    maquina = Maquina(
        codigo="Mq_01",
        nome="Misturador",
        valor_compra=Decimal("1200"),
        meses_depreciacao=12,
        manutencao_mensal=Decimal("0"),
        custo_energia_mensal=Decimal("0"),
        horas_uteis_mensais=Decimal("100"),
    )
    funcionario = Funcionario(
        codigo_fopag="F01",
        setor_id=setor.id,
        nome="Fulana",
        cargo="Auxiliar",
        custo_mensal=Decimal("1000"),
        horas_uteis_mensais=Decimal("100"),
    )
    session.add_all([processo, ambiente, maquina, funcionario])
    session.flush()
    return processo, ambiente, maquina, funcionario


def test_custo_maquina_ambiente_mao_de_obra(session):
    processo, ambiente, maquina, funcionario = _setup_recursos(session)

    produto = Produto(codigo="Produ_001", nome="Teste", tipo="acabado", rendimento_un=Decimal("10"))
    session.add(produto)
    session.flush()

    session.add(RoteiroMaquina(produto_id=produto.id, processo_id=processo.id, maquina_id=maquina.id, tempo_horas=Decimal("2")))
    session.add(RoteiroAmbiente(produto_id=produto.id, processo_id=processo.id, ambiente_id=ambiente.id, tempo_horas=Decimal("1")))
    session.add(RoteiroMaoDeObra(produto_id=produto.id, processo_id=processo.id, funcionario_id=funcionario.id, tempo_horas=Decimal("3")))
    session.commit()

    custo = calcular_custo_produto(session, produto)

    # maquina: valor_compra/meses=100/mes, custo_hora=1 -> 2h = 2
    assert custo.custo_maquina == Decimal("2")
    # ambiente: 1000/100=10/h -> 1h = 10
    assert custo.custo_ambiente == Decimal("10")
    # mao de obra: 1000/100=10/h -> 3h = 30
    assert custo.custo_mao_de_obra == Decimal("30")
    assert custo.custo_insumos == Decimal("0")
    assert custo.custo_lote_total == Decimal("42")
    assert custo.custo_unitario(produto) == Decimal("4.2")


def test_custo_insumo_comprado(session):
    processo, ambiente, maquina, funcionario = _setup_recursos(session)
    insumo = Insumo(
        codigo="ING_01",
        nome="Aveia",
        tipo="ingrediente",
        valor_compra_unitario=Decimal("2"),
        frete=Decimal("0.5"),
        ipi_pct=Decimal("0"),
        icms_pct=Decimal("0"),
    )
    session.add(insumo)
    session.flush()

    produto = Produto(codigo="Produ_002", nome="Teste 2", tipo="acabado", rendimento_un=Decimal("1"))
    session.add(produto)
    session.flush()
    session.add(RoteiroInsumo(produto_id=produto.id, processo_id=processo.id, insumo_id=insumo.id, quantidade_kg=Decimal("10")))
    session.commit()

    custo = calcular_custo_produto(session, produto)

    # custo_final do insumo = 2 + 0.5 = 2.5; 10kg * 2.5 = 25
    assert custo.custo_insumos == Decimal("25")
    assert custo.custo_lote_total == Decimal("25")


def test_custo_semi_acabado_como_insumo(session):
    """BOM em 2 níveis: um produto acabado consome um semiacabado como insumo (por kg)."""
    processo, ambiente, maquina, funcionario = _setup_recursos(session)
    insumo = Insumo(
        codigo="ING_02",
        nome="Coco",
        tipo="ingrediente",
        valor_compra_unitario=Decimal("3"),
        frete=Decimal("0"),
        ipi_pct=Decimal("0"),
        icms_pct=Decimal("0"),
    )
    session.add(insumo)
    session.flush()

    semi_acabado = Produto(codigo="PSA_001", nome="Coco Ralado", tipo="semi_acabado", rendimento_kg=Decimal("5"))
    session.add(semi_acabado)
    session.flush()
    session.add(
        RoteiroInsumo(produto_id=semi_acabado.id, processo_id=processo.id, insumo_id=insumo.id, quantidade_kg=Decimal("5"))
    )
    # custo do lote do semiacabado = 5kg * 3 = 15; custo por kg = 15/5 = 3

    produto_final = Produto(codigo="Produ_003", nome="Barra", tipo="acabado", rendimento_un=Decimal("1"))
    session.add(produto_final)
    session.flush()
    session.add(
        RoteiroInsumo(
            produto_id=produto_final.id,
            processo_id=processo.id,
            insumo_produto_id=semi_acabado.id,
            quantidade_kg=Decimal("2"),
        )
    )
    session.commit()

    custo = calcular_custo_produto(session, produto_final)

    # 2kg do semiacabado * custo/kg (3) = 6
    assert custo.custo_insumos == Decimal("6")
    assert custo.custo_lote_total == Decimal("6")


def test_ciclo_no_roteiro_levanta_erro(session):
    processo, ambiente, maquina, funcionario = _setup_recursos(session)

    a = Produto(codigo="Produ_A", nome="A", tipo="semi_acabado", rendimento_kg=Decimal("1"))
    b = Produto(codigo="Produ_B", nome="B", tipo="semi_acabado", rendimento_kg=Decimal("1"))
    session.add_all([a, b])
    session.flush()

    session.add(RoteiroInsumo(produto_id=a.id, processo_id=processo.id, insumo_produto_id=b.id, quantidade_kg=Decimal("1")))
    session.add(RoteiroInsumo(produto_id=b.id, processo_id=processo.id, insumo_produto_id=a.id, quantidade_kg=Decimal("1")))
    session.commit()

    with pytest.raises(RuntimeError):
        calcular_custo_produto(session, a)
