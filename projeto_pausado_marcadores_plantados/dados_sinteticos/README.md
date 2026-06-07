# dados_sinteticos/

Gerador da base sintética **com marcadores plantados** (verdade-base) e o **validador de
integridade relacional** (FKs, cronologia, faixas válidas) que garante a fidelidade REDS no final.

Aqui mora a "verdade conhecida": quais marcadores foram plantados, a relação marcador→HLY, e as
variáveis-ruído. Essa verdade é o gabarito contra o qual o BFSS e o MOFSS serão validados.

> A definir antes de implementar (ver `ESTADO_ATUAL.md`, seção 5). Reaproveitar o que servir de
> `old/banco/db_schema.py` (schema) e `old/banco/validator.py` (validação relacional).
