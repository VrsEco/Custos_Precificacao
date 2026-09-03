"""Popula o banco local com dados fictícios para explorar o schema e testar a CLI.

Não usa dados reais da empresa. Rode com: python scripts/seed_dev.py
"""

from decimal import Decimal

from custos_precificacao.db import SessionLocal
from custos_precificacao.models import (
    Ambiente,
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


def main() -> None:
    with SessionLocal() as session:
        setor = Setor(codigo="Set_01", nome="Granola (exemplo)")
        session.add(setor)
        session.flush()

        processo = Processo(codigo="Proce_01", setor_id=setor.id, nome="Mistura (exemplo)")
        ambiente = Ambiente(
            codigo="Inst_01", nome="Fábrica (exemplo)",
            valor_rateado_mensal=Decimal("1000"), horas_uteis_mensais=Decimal("200"),
        )
        maquina = Maquina(
            codigo="Mq_01", nome="Misturador (exemplo)",
            valor_compra=Decimal("6000"), meses_depreciacao=60,
            manutencao_mensal=Decimal("20"), custo_energia_mensal=Decimal("10"),
            horas_uteis_mensais=Decimal("200"),
        )
        funcionario = Funcionario(
            codigo_fopag="F01", setor_id=setor.id, nome="Fulano (exemplo)", cargo="Auxiliar",
            custo_mensal=Decimal("2000"), horas_uteis_mensais=Decimal("160"),
        )
        insumo = Insumo(
            codigo="ING_01", nome="Aveia (exemplo)", tipo="ingrediente",
            valor_compra_unitario=Decimal("3"), frete=Decimal("0.2"),
        )
        session.add_all([processo, ambiente, maquina, funcionario, insumo])
        session.flush()

        semi_acabado = Produto(codigo="PSA_001", nome="Mix Base (exemplo)", tipo="semi_acabado", rendimento_kg=Decimal("10"))
        session.add(semi_acabado)
        session.flush()
        session.add(RoteiroInsumo(produto_id=semi_acabado.id, processo_id=processo.id, insumo_id=insumo.id, quantidade_kg=Decimal("10")))

        produto = Produto(codigo="Produ_001", nome="Granola 250g (exemplo)", tipo="acabado", rendimento_un=Decimal("40"))
        session.add(produto)
        session.flush()
        session.add(RoteiroMaquina(produto_id=produto.id, processo_id=processo.id, maquina_id=maquina.id, tempo_horas=Decimal("1")))
        session.add(RoteiroAmbiente(produto_id=produto.id, processo_id=processo.id, ambiente_id=ambiente.id, tempo_horas=Decimal("1")))
        session.add(RoteiroMaoDeObra(produto_id=produto.id, processo_id=processo.id, funcionario_id=funcionario.id, tempo_horas=Decimal("2")))
        session.add(RoteiroInsumo(produto_id=produto.id, processo_id=processo.id, insumo_produto_id=semi_acabado.id, quantidade_kg=Decimal("5")))

        session.commit()
        print("Seed concluído: 1 semiacabado + 1 produto acabado de exemplo.")


if __name__ == "__main__":
    main()
