# Contexto da Sessão Antigravity

Este arquivo guarda o contexto da sessão atual de Inteligência Artificial, para que você possa continuar os trabalhos na mesma branch a partir de outra máquina.

## Status Atual
- **Trilha Principal (Meta-Otimização FSS)**: Otimizamos com sucesso os hiperparâmetros (`w_in`, `c1`, `c2`, `LAMBDA`) do script PSO (`pso_diabetes.py`) usando o algoritmo FSS (Fish School Search). 
- **Onde o código está**: Toda a rotina do FSS e geração das novas análises foram encapsuladas na pasta `plano_b_pso_diabetes/meta_fss_pso`.
- **Ajuste na visualização**: Criamos o script `adicionar_aba_meta.py` e geramos uma nova versão do `pso_visualizacao.html` na pasta `meta_fss_pso`, contendo uma aba exclusiva sobre a otimização de hiperparâmetros (FSS).

## Tarefas (Task List)
- [x] Criar pasta `meta_fss_pso/` (movido para `plano_b_pso_diabetes/meta_fss_pso/`)
- [x] Criar e executar `meta_fss_pso/meta_fss_pso.py`
  - [x] Pipeline de dados (reutilizar lógica do pso_diabetes.py)
  - [x] PSO interno leve (parametrizável: w_in, c1, c2, lam)
  - [x] Função `avaliar_hp()` com CV-3
  - [x] Meta-FSS com movimentos individual, instintivo e volitivo
  - [x] PSO completo para comparação (padrão vs. meta-otimizado)
  - [x] `main()` e `salvar_saidas()`
- [x] Executar script e avaliar `../RESULTADOS_META.md` gerado.
- [x] Atualizar a visualização em HTML do PSO (`pso_visualizacao.html`) com uma nova aba para análises de hiperparâmetros.

## Próximos Passos (Backlog Ativo)
1. **Implementar Regularização L1 / Elastic Net**: No PSO, atualmente temos uma regularização L2 (`LAMBDA`). O próximo passo aprovado no backlog é tentar introduzir a regularização L1, seja em substituição ou adotando um modelo Elastic Net, o que forçaria pesos não importantes a caírem para zero (seleção de features explícita ao longo do PSO).

## Diretrizes de Codificação Relembradas
- Não alterar as funções core de *Fitness* e *Wellness*.
- Continuar trabalhando dentro da trilha evolutiva (diretório `plano_b_pso_diabetes/`).
- Escopo limitado a algoritmos evolucionários e do universo de Computação Natural.

*(Pode deletar este arquivo se achar desnecessário, ele apenas serve para que o próximo Agente/Máquina saiba exatamente de onde você parou).*
