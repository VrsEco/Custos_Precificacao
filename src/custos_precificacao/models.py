from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


Money = Numeric(14, 6)


class Setor(Base):
    __tablename__ = "setor"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True)
    nome: Mapped[str] = mapped_column(String(200))


class Processo(Base):
    __tablename__ = "processo"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True)
    setor_id: Mapped[int] = mapped_column(ForeignKey("setor.id"))
    nome: Mapped[str] = mapped_column(String(200))


class Ambiente(Base):
    """Instalação/espaço físico. Custo/hora = valor mensal rateado / horas úteis mensais."""

    __tablename__ = "ambiente"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True)
    nome: Mapped[str] = mapped_column(String(200))
    valor_rateado_mensal: Mapped[Decimal] = mapped_column(Money, default=0)
    horas_uteis_mensais: Mapped[Decimal] = mapped_column(Money, default=0)

    @property
    def custo_hora(self) -> Decimal:
        if not self.horas_uteis_mensais:
            return Decimal(0)
        return self.valor_rateado_mensal / self.horas_uteis_mensais


class Maquina(Base):
    """Custo/hora = (depreciação mensal + manutenção + energia) / horas úteis mensais."""

    __tablename__ = "maquina"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True)
    nome: Mapped[str] = mapped_column(String(200))
    ambiente_id: Mapped[int | None] = mapped_column(ForeignKey("ambiente.id"), nullable=True)
    setor_id: Mapped[int | None] = mapped_column(ForeignKey("setor.id"), nullable=True)
    valor_compra: Mapped[Decimal] = mapped_column(Money, default=0)
    meses_depreciacao: Mapped[int] = mapped_column(default=1)
    manutencao_mensal: Mapped[Decimal] = mapped_column(Money, default=0)
    custo_energia_mensal: Mapped[Decimal] = mapped_column(Money, default=0)
    horas_uteis_mensais: Mapped[Decimal] = mapped_column(Money, default=0)

    @property
    def custo_hora(self) -> Decimal:
        if not self.horas_uteis_mensais:
            return Decimal(0)
        depreciacao_mensal = self.valor_compra / self.meses_depreciacao if self.meses_depreciacao else Decimal(0)
        custo_mensal = depreciacao_mensal + self.manutencao_mensal + self.custo_energia_mensal
        return custo_mensal / self.horas_uteis_mensais


class Funcionario(Base):
    """Custo/hora = custo mensal total (salário + encargos) / horas úteis mensais."""

    __tablename__ = "funcionario"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo_fopag: Mapped[str] = mapped_column(String(20), unique=True)
    setor_id: Mapped[int] = mapped_column(ForeignKey("setor.id"))
    nome: Mapped[str] = mapped_column(String(200))
    cargo: Mapped[str] = mapped_column(String(200))
    custo_mensal: Mapped[Decimal] = mapped_column(Money, default=0)
    horas_uteis_mensais: Mapped[Decimal] = mapped_column(Money, default=0)

    @property
    def custo_hora(self) -> Decimal:
        if not self.horas_uteis_mensais:
            return Decimal(0)
        return self.custo_mensal / self.horas_uteis_mensais


class Insumo(Base):
    """Matéria-prima ou embalagem comprada de terceiros.

    custo_final é uma simplificação: preço + frete + IPI (%) - crédito de ICMS (%).
    A regra fiscal exata pode ser refinada quando os dados reais forem inseridos.
    """

    __tablename__ = "insumo"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True)
    nome: Mapped[str] = mapped_column(String(200))
    tipo: Mapped[str] = mapped_column(String(20))  # 'ingrediente' | 'embalagem'
    valor_compra_unitario: Mapped[Decimal] = mapped_column(Money, default=0)
    frete: Mapped[Decimal] = mapped_column(Money, default=0)
    ipi_pct: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=0)
    icms_pct: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=0)

    __table_args__ = (CheckConstraint("tipo in ('ingrediente', 'embalagem')", name="ck_insumo_tipo"),)

    @property
    def custo_final(self) -> Decimal:
        ipi_valor = self.valor_compra_unitario * self.ipi_pct
        icms_credito = self.valor_compra_unitario * self.icms_pct
        return self.valor_compra_unitario + self.frete + ipi_valor - icms_credito


class Produto(Base):
    """Produto acabado ou semiacabado (usado como insumo de outro produto)."""

    __tablename__ = "produto"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True)
    nome: Mapped[str] = mapped_column(String(300))
    tipo: Mapped[str] = mapped_column(String(20))  # 'acabado' | 'semi_acabado'
    rendimento_kg: Mapped[Decimal | None] = mapped_column(Money, nullable=True)
    rendimento_un: Mapped[Decimal | None] = mapped_column(Money, nullable=True)
    qtd_estimada_producao_mes: Mapped[Decimal | None] = mapped_column(Money, nullable=True)

    __table_args__ = (CheckConstraint("tipo in ('acabado', 'semi_acabado')", name="ck_produto_tipo"),)

    roteiro_maquina: Mapped[list["RoteiroMaquina"]] = relationship(
        back_populates="produto", foreign_keys="RoteiroMaquina.produto_id"
    )
    roteiro_ambiente: Mapped[list["RoteiroAmbiente"]] = relationship(
        back_populates="produto", foreign_keys="RoteiroAmbiente.produto_id"
    )
    roteiro_mao_de_obra: Mapped[list["RoteiroMaoDeObra"]] = relationship(
        back_populates="produto", foreign_keys="RoteiroMaoDeObra.produto_id"
    )
    roteiro_insumo: Mapped[list["RoteiroInsumo"]] = relationship(
        back_populates="produto", foreign_keys="RoteiroInsumo.produto_id"
    )


class RoteiroMaquina(Base):
    __tablename__ = "roteiro_maquina"

    id: Mapped[int] = mapped_column(primary_key=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produto.id"))
    processo_id: Mapped[int] = mapped_column(ForeignKey("processo.id"))
    ordem: Mapped[int] = mapped_column(default=0)
    maquina_id: Mapped[int] = mapped_column(ForeignKey("maquina.id"))
    tempo_horas: Mapped[Decimal] = mapped_column(Money, default=0)

    produto: Mapped["Produto"] = relationship(back_populates="roteiro_maquina", foreign_keys=[produto_id])
    maquina: Mapped["Maquina"] = relationship()


class RoteiroAmbiente(Base):
    __tablename__ = "roteiro_ambiente"

    id: Mapped[int] = mapped_column(primary_key=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produto.id"))
    processo_id: Mapped[int] = mapped_column(ForeignKey("processo.id"))
    ordem: Mapped[int] = mapped_column(default=0)
    ambiente_id: Mapped[int] = mapped_column(ForeignKey("ambiente.id"))
    tempo_horas: Mapped[Decimal] = mapped_column(Money, default=0)

    produto: Mapped["Produto"] = relationship(back_populates="roteiro_ambiente", foreign_keys=[produto_id])
    ambiente: Mapped["Ambiente"] = relationship()


class RoteiroMaoDeObra(Base):
    __tablename__ = "roteiro_mao_de_obra"

    id: Mapped[int] = mapped_column(primary_key=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produto.id"))
    processo_id: Mapped[int] = mapped_column(ForeignKey("processo.id"))
    ordem: Mapped[int] = mapped_column(default=0)
    funcionario_id: Mapped[int] = mapped_column(ForeignKey("funcionario.id"))
    tempo_horas: Mapped[Decimal] = mapped_column(Money, default=0)

    produto: Mapped["Produto"] = relationship(back_populates="roteiro_mao_de_obra", foreign_keys=[produto_id])
    funcionario: Mapped["Funcionario"] = relationship()


class RoteiroInsumo(Base):
    """Consumo de insumo comprado (insumo_id) OU de outro produto/semiacabado (insumo_produto_id).

    Exatamente um dos dois deve ser preenchido.
    """

    __tablename__ = "roteiro_insumo"

    id: Mapped[int] = mapped_column(primary_key=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produto.id"))
    processo_id: Mapped[int] = mapped_column(ForeignKey("processo.id"))
    ordem: Mapped[int] = mapped_column(default=0)
    insumo_id: Mapped[int | None] = mapped_column(ForeignKey("insumo.id"), nullable=True)
    insumo_produto_id: Mapped[int | None] = mapped_column(ForeignKey("produto.id"), nullable=True)
    quantidade_kg: Mapped[Decimal] = mapped_column(Money, default=0)

    __table_args__ = (
        CheckConstraint(
            "(insumo_id IS NOT NULL) <> (insumo_produto_id IS NOT NULL)",
            name="ck_roteiro_insumo_fonte_unica",
        ),
    )

    produto: Mapped["Produto"] = relationship(back_populates="roteiro_insumo", foreign_keys=[produto_id])
    insumo: Mapped["Insumo | None"] = relationship(foreign_keys=[insumo_id])
    insumo_produto: Mapped["Produto | None"] = relationship(foreign_keys=[insumo_produto_id])


class CusteioExecucao(Base):
    __tablename__ = "custeio_execucao"

    id: Mapped[int] = mapped_column(primary_key=True)
    executado_em: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    observacao: Mapped[str | None] = mapped_column(String(500), nullable=True)


class CusteioProduto(Base):
    """Resultado de uma rodada de custeio para um produto.

    custo_maquina/ambiente/mao_de_obra/insumos são totais do lote/receita (não por unidade).
    custo_total_unitario é o custo do lote dividido pelo rendimento (em unidades vendáveis
    quando disponível, senão em kg).
    """

    __tablename__ = "custeio_produto"

    id: Mapped[int] = mapped_column(primary_key=True)
    execucao_id: Mapped[int] = mapped_column(ForeignKey("custeio_execucao.id"))
    produto_id: Mapped[int] = mapped_column(ForeignKey("produto.id"))
    custo_maquina: Mapped[Decimal] = mapped_column(Money, default=0)
    custo_ambiente: Mapped[Decimal] = mapped_column(Money, default=0)
    custo_mao_de_obra: Mapped[Decimal] = mapped_column(Money, default=0)
    custo_insumos: Mapped[Decimal] = mapped_column(Money, default=0)
    custo_total_unitario: Mapped[Decimal] = mapped_column(Money, default=0)

    produto: Mapped["Produto"] = relationship()
