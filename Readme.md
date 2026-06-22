# 📊 Dashboard Estatístico em Shiny for Python

## 📌 Sobre o projeto

Este repositório contém o desenvolvimento de um **dashboard estatístico interativo** em **Python**, utilizando o framework **Shiny for Python**, como atividade avaliativa da disciplina.

O dashboard foi construído com o objetivo de permitir a **análise estatística de bases de dados carregadas pelo próprio usuário**, contemplando desde análises descritivas até procedimentos inferenciais e regressão linear simples.

A aplicação permite:

* **Análise descritiva** de uma variável quantitativa;
* **Teste de hipóteses para a média populacional com variância conhecida**;
* **Intervalo de confiança normal para a média populacional**;
* **Regressão linear simples** entre duas variáveis quantitativas.


## 👥 Integrantes

* **Heitor Leonny Lima Pereira**
* **Lucas Gabriel Gomes dos Passos**
---

## 🎥 Vídeo de demonstração

O vídeo demonstrando o funcionamento completo do dashboard pode ser acessado no link abaixo:

🔗 **YouTube:** [inserir link do vídeo aqui]

---

## 🔗 Repositório do projeto

🔗 **GitHub:** https://github.com/heitorleonny/estatistica

---

# 🚀 Funcionalidades do Dashboard

## 1) Análise Descritiva de uma Variável

O dashboard permite ao usuário:

* carregar um arquivo de dados do próprio computador;
* selecionar uma variável quantitativa;
* gerar um **histograma** da variável selecionada;
* gerar um **boxplot** da variável selecionada;
* visualizar as principais **estatísticas descritivas**:

  * média;
  * mediana;
  * desvio-padrão;
  * tamanho da amostra;
  * valor mínimo;
  * valor máximo.

---

## 2) Teste de Hipóteses para a Média com Variância Conhecida

Para uma variável quantitativa selecionada, o dashboard realiza um **teste Z para a média populacional**, assumindo **variância conhecida**.

O usuário pode informar:

* **variância populacional**;
* **tipo de teste**:

  * bilateral;
  * unilateral à direita;
  * unilateral à esquerda;
* **valor de μ₀**;
* **nível de significância (α)**.

O dashboard retorna, no mínimo:

* estatística do teste;
* decisão do teste.

Além disso, a aplicação também apresenta o **p-valor** e uma **visualização da distribuição normal com a região crítica do teste**.

---

## 3) Intervalo de Confiança Normal para a Média

Para a variável quantitativa selecionada, o dashboard constrói um **intervalo de confiança normal para a média populacional**, considerando variância populacional conhecida.

O usuário pode definir o **nível de confiança**, e o sistema retorna:

* limite inferior;
* limite superior;
* nível de confiança utilizado.

---

## 4) Regressão Linear Simples

O dashboard também permite ajustar um modelo de **regressão linear simples** entre duas variáveis quantitativas da base de dados:

* uma variável escolhida como **resposta (Y)**;
* outra variável escolhida como **explicativa (X)**.

O sistema retorna:

* **coeficiente de correlação (R)**;
* **coeficiente de determinação (R²)**;
* **equação da reta ajustada**.

Além disso, também gera:

* **gráfico de dispersão** entre X e Y;
* **linha de regressão ajustada** sobre o gráfico.

---

# 🛠️ Tecnologias utilizadas

Este projeto foi desenvolvido utilizando as seguintes tecnologias e bibliotecas:

* **Python**
* **Shiny for Python**
* **Pandas**
* **NumPy**
* **Matplotlib**
* **SciPy**
* **OpenPyXL**
* **xlrd** (para leitura de arquivos `.xls`)

---

# 📂 Estrutura do projeto

```bash
.
├── app.py                # Arquivo principal do dashboard
├── README.md             # Documentação do projeto
└── requirements.txt      # Dependências do projeto (opcional, se criado)
```

---

# ▶️ Como executar o projeto localmente

## 1. Clone este repositório

```bash
git clone <link-do-repositorio>
cd <nome-da-pasta>
```

---

## 2. Crie e ative um ambiente virtual (recomendado)

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / Mac

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Instale as dependências

Se o projeto possuir um arquivo `requirements.txt`, execute:

```bash
pip install -r requirements.txt
```

Caso não exista, instale manualmente as bibliotecas abaixo:

```bash
pip install shiny pandas numpy matplotlib scipy openpyxl xlrd
```

---

## 4. Execute o dashboard

Com o ambiente virtual ativado e dentro da pasta do projeto, rode:

```bash
shiny run --reload app.py
```

Se necessário, também pode funcionar com:

```bash
python -m shiny run --reload app.py
```

---

## 5. Acesse no navegador

Após a execução, o terminal exibirá um endereço local, normalmente semelhante a:

```bash
http://127.0.0.1:8000
```

Basta abrir esse link no navegador para utilizar o dashboard.

---

# 📁 Formatos de arquivo suportados

O dashboard permite o carregamento de arquivos nos formatos:

* `.csv`
* `.xlsx`
* `.xls`

---

# 📸 Interface do dashboard

O dashboard foi organizado em **quatro abas principais**, correspondentes às etapas da atividade:

1. **Análise Descritiva**
2. **Teste de Hipóteses**
3. **Intervalo de Confiança**
4. **Regressão Linear Simples**

> Você pode adicionar aqui prints da aplicação em funcionamento para deixar o repositório mais completo.

Exemplo:

```md
## Tela inicial
![Tela inicial](caminho/da/imagem.png)

## Aba de regressão
![Regressão](caminho/da/imagem2.png)
```

---

# 📌 Observações importantes

* O projeto foi desenvolvido para execução em **Python 3.10+**.
* O tratamento e a leitura dos dados são feitos diretamente no dashboard, sem necessidade de edição prévia da planilha.
* Para arquivos no formato `.xls`, é necessário ter a biblioteca **xlrd** instalada.
* As colunas numéricas da base são identificadas dinamicamente pelo sistema, e colunas textuais com valores numéricos também podem ser convertidas automaticamente quando possível.

---

# 🧠 Lógica estatística implementada

O dashboard contempla os seguintes procedimentos estatísticos:

* **Estatística descritiva** para variáveis quantitativas;
* **Teste Z para média com variância conhecida**;
* **Intervalo de confiança normal para média com variância conhecida**;
* **Regressão linear simples** com cálculo de correlação e coeficiente de determinação.

---

# 📚 Referência principal utilizada

A principal referência para construção da aplicação foi a documentação oficial do **Shiny for Python**:

🔗 https://shiny.posit.co/py/

---

# ✅ Requisitos da atividade contemplados

Este projeto foi desenvolvido com base no briefing da atividade e contempla:

* upload de arquivo pelo usuário;
* análise descritiva de variável quantitativa;
* histograma e boxplot;
* estatísticas descritivas;
* teste de hipóteses para média com variância conhecida;
* intervalo de confiança normal para média;
* regressão linear simples;
* gráfico de dispersão com reta de regressão.

---

# 📬 Entrega

Conforme solicitado na atividade, a entrega final deve conter:

* comentário com o **nome dos integrantes**;
* **link do vídeo no YouTube**;
* **link do repositório público no GitHub**.

---

# ✍️ Observação final

Este repositório foi desenvolvido para fins acadêmicos, como parte de uma atividade prática envolvendo **visualização de dados, estatística inferencial e construção de dashboards interativos em Python**.
