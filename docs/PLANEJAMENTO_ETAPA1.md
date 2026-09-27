# Etapa 1 — Planejamento (dados para a planilha do Google Classroom)

| Campo | Conteúdo |
|---|---|
| **Integrantes** | Pedro Paulo · Yuri Aguiar · João Rath — turma CC6NA |
| **Título** | ValidaFrete — Validador de Cadastros de Fretes com Expressões Regulares |
| **Descrição** | Aplicação web que valida planilhas e valores de cadastros de fretes de transportadoras (CNPJ alfanumérico do cliente, placa do veículo antiga/Mercosul, telefone do motorista com DDD válido, data da coleta com dia compatível com o mês e valor do frete em R$). Cada campo é conferido por uma Expressão Regular própria; em caso de erro, o programa simula o AFNε equivalente para indicar a posição exata da falha, e gera um relatório CSV com os registros inválidos. |
| **Linguagem** | Python 3 |
| **Repositório** | https://github.com/<usuario>/validafrete *(preencher)* |
| **Requisitos funcionais / ambiente** | Python 3.10+, Flask 3 (interface web), módulo `re` da biblioteca padrão (motor de ER), pytest (testes), Graphviz (diagramas dos AFNε), VS Code, Git/GitHub |
