# dados_sinteticos/

Gerador da base sintética **com marcadores plantados** (verdade-base) e o **validador de
integridade relacional** (FKs, cronologia, faixas válidas) que garante a fidelidade REDS no final.

Aqui mora a "verdade conhecida": quais marcadores foram plantados, a relação marcador→HLY, e as
variáveis-ruído. Essa verdade é o gabarito contra o qual o BFSS e o MOFSS serão validados.

> ✅ **IMPLEMENTADO em 2026-06-07.**
> - **Modelo numérico decidido:** `contexto/MODELO_NUMERICO.md` (M1/M2/M3, fórmula de ΔHLY, parâmetros, evidências).
> - **Gerador:** `gerar_base.py` (usa `../simulador_hly/modelo_hly.py`). Rode `python3 gerar_base.py`.
> - **Saída** (`saida/`): `base_bfss.csv` (entrada do BFSS), `reds_dm1_sintetico.db` (banco relacional REDS
>   íntegro), `gabarito_marcadores.json` (relevantes×ruído), `pacientes_resumo.csv`.
> - **Validação:** `../validacao/validar_base.py` (integridade relacional + recuperabilidade do sinal).
