Reproduzir uma planilha de análise de FIIs em um dashboard Python, utilizando dados coletados do site Investidor10.


https://investidor10.com.br/
Descrição geral
O estudante deverá desenvolver um dashboard em Python com , permitindo consultar FIIs, simular aportes mensais, montar uma carteira e calcular preço teto.

Pode usar, por exemplo:streamlit
pandas
requests
beautifulsoup4
plotly
Janela 1 — Simulação de aporte mensal em um FII

O usuário deverá informar:Ticker do FII
Quantidade de cotas compradas mensalmente
Quantidade de meses da projeção


O sistema deverá buscar automaticamente:Cotação atual
Dividend Yield %


O dashboard deverá calcular:Investimento mensal = preço atual × quantidade de cotas
Quantidade total de cotas acumuladas
Total investido
Renda mensal estimada
Renda acumulada no período


Exemplo:Ticker: MXRF11
Quantidade mensal: 10 cotas
Projeção: 240 meses
Janela 2 — Carteira com múltiplos FIIs
O usuário deverá escolher entre .
Para cada FII, o usuário informará:Ticker
Quantidade de cotas

A tabela deverá se ajustar automaticamente ao número de FIIs escolhido.
A tabela final deverá conter:FII
Preço
Quantidade
Investimento
Proventos
Renda Mensal

Cálculos:Investimento = Preço × Quantidade

Proventos = Dividendos estimados por cota

Renda Mensal = Proventos × Quantidade

Ao final, o sistema deverá mostrar também:Investimento total da carteira
Renda mensal total
Dividend Yield médio da carteira
Janela 3 — Cálculo de preço teto
Nesta aba, o sistema deverá calcular o preço teto de cada FII conforme a lógica da planilha.
A tabela deverá conter as colunas:FII
P/VP
PREÇO
DIVIDENDO12M%
DIVIDENDO12M(R$)
IPCA
IPCA+
PRÊMIO
PREÇO TETO
MARGEM DE SEG.
RegrasIPCAFII de tijolo: IPCA = 0%
FII de papel: IPCA = 5%
IPCA+IPCA+ = 7%
Prêmio de risco
O usuário deverá informar o prêmio, seguindo a classificação:Prêmio baixo: 1%
FII grande, com patrimônio acima de R$ 2 bilhões, e DY menor ou igual a 12%.

Prêmio médio: 3%
FII médio, de papel ou tijolo, pagando até 16% de DY.

Prêmio alto: 5%
Demais casos.
Fórmula sugeridaTaxa requerida = IPCA + IPCA+ + Prêmio

Preço teto = Dividendo12M(R$) / Taxa requerida

Margem de segurança = (Preço teto - Preço atual) / Preço atual
Entregáveis


O estudante deverá entregar:1. Código-fonte do dashboard em Python
2. Arquivo requirements.txt
3. Prints das três janelas funcionando
4. Breve explicação da lógica usada no web scraping
5. Comentários no código explicando os principais cálculos
Critérios de avaliaçãoWeb scraping funcionando: 2,0 pontos
Janela 1 funcionando: 2,0 pontos
Janela 2 funcionando: 2,0 pontos
Janela 3 funcionando: 2,0 pontos
Organização visual do dashboard: 1,0 ponto
Código comentado e bem estruturado: 1,0 ponto