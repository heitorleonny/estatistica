# Dashboard de FIIs

Dashboard Python para análise de Fundos de Investimento Imobiliário com dados ao vivo do Investidor10.

## Requisitos

- Python 3.10+

## Instalação

```bash
pip3 install -r requirements.txt
python3 -m playwright install chromium
```

## Rodar

```bash
streamlit run app.py
```

Acesse **http://localhost:8501** no navegador.

## Abas

| Aba | O que faz |
|-----|-----------|
| 📈 Simulação | Projeta patrimônio e renda ao aportar cotas mensalmente |
| 💼 Carteira | Monta carteira com 4–10 FIIs e calcula renda mensal total |
| 🎯 Preço Teto | Calcula preço teto e margem de segurança de cada FII |

> Os dados são buscados ao vivo via web scraping. A primeira consulta de cada FII demora ~10 segundos; depois fica em cache por 1 hora.
