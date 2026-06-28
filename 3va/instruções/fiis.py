# pip install pandas playwright openpyxl
# playwright install chromium

import re
import time
import math
import pandas as pd
from playwright.sync_api import sync_playwright


fiis = [
    "GARE11",
    "GGRC11",
    "XPML11",
    "BTLG11",
    "BTCI11",
    "KNRI11",
    "RECR11",
    "TRXF11",
    "VGHF11",
    "RBVA11",
    "MXRF11",
    "LVBI11",
    "PORD11",
    "HGLG11",
    "KNCR11",
    "SNAG11",
    "HSLG11"
]



ipca_mais = 0.07
pausa = 1

ipca_por_fii = {
    # Exemplo de sobrescrita manual:
    # "MXRF11": 0.025,
}


premio_por_fii = {
    "default": 0.01,

    # =========================
    # HIGH GRADE = 0.01
    # =========================
    "XPML11": 0.01,
    "BTLG11": 0.01,
    "KNRI11": 0.01,
    "LVBI11": 0.01,
    "HGLG11": 0.01,
    "HSLG11": 0.01,

    # =========================
    # MIDDLE GRADE = 0.03
    # =========================
    "GARE11": 0.03,
    "GGRC11": 0.03,
    "BTCI11": 0.03,
    "TRXF11": 0.03,
    "RBVA11": 0.03,
    "KNCR11": 0.03,
    "SNAG11": 0.03,

    # =========================
    # HIGH YIELD = 0.05
    # =========================
    "RECR11": 0.05,
    "VGHF11": 0.05,
    "MXRF11": 0.05,
    "PORD11": 0.05,
}



def br_to_float(valor):
    if valor is None:
        return math.nan

    txt = str(valor).strip()
    txt = txt.replace("R$", "").replace("%", "").strip()

    if txt in ["", "-", "N/A", "NaN"]:
        return math.nan

    txt = txt.replace(".", "").replace(",", ".")

    try:
        return float(txt)
    except ValueError:
        return math.nan


def percent_to_decimal(valor):
    x = br_to_float(valor)

    if pd.isna(x):
        return math.nan

    return x / 100


def limpar_tela(page):
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
    except Exception:
        pass

    try:
        page.evaluate("""
            () => {
                const banner = document.querySelector('#guest-user-banner-irpf');
                if (banner) banner.remove();

                const backdrop = document.querySelector('.modal-backdrop');
                if (backdrop) backdrop.remove();

                document.body.classList.remove('modal-open');
                document.body.style.overflow = 'auto';
                document.body.style.paddingRight = '0px';
            }
        """)
    except Exception:
        pass


def extrair_valor_por_rotulo(texto, rotulos):
    texto_limpo = re.sub(r"\s+", " ", texto)

    for rotulo in rotulos:
        padrao = rf"{rotulo}\s*[:\-]?\s*(R\$)?\s*(-?[\d\.\,]+%?)"

        m = re.search(
            padrao,
            texto_limpo,
            flags=re.IGNORECASE
        )

        if m:
            return m.group(2)

    return None


def extrair_tipo_fundo(texto):
    texto_limpo = re.sub(r"\s+", " ", texto)

    padroes = [
        r"Tipo de fundo\s*[:\-]?\s*([A-Za-zÀ-ÿ\s]+)",
        r"Tipo\s*[:\-]?\s*([A-Za-zÀ-ÿ\s]+)",
    ]

    for padrao in padroes:
        m = re.search(
            padrao,
            texto_limpo,
            flags=re.IGNORECASE
        )

        if m:
            return m.group(1).strip().lower()

    return ""


def extrair_percentual_ativo_fii(page):
    """
    Extrai o percentual associado ao item:
    <p class="legend-name">FII</p>

    Caso não encontre, retorna 100% (= 1.00),
    o que implicará IPCA = 5%.
    """

    try:
        valor = page.evaluate("""
            () => {

                const todosNomes =
                    Array.from(document.querySelectorAll('.legend-name'));

                const todosValores =
                    Array.from(document.querySelectorAll('.legend-value'));

                for (let i = 0; i < todosNomes.length; i++) {

                    const nome =
                        todosNomes[i].innerText.trim().toUpperCase();

                    if (nome === 'FII') {

                        if (todosValores[i]) {
                            return todosValores[i].innerText.trim();
                        }
                    }
                }

                return null;
            }
        """)

        # NÃO encontrou FII
        # assume 100%
        if valor is None:
            return 1.00

        return percent_to_decimal(valor)

    except Exception:
        # fallback conservador
        return 1.00


def ipca_por_percentual_fii(percentual_fii):
    if pd.isna(percentual_fii):
        return math.nan

    if percentual_fii >= 0.00 and percentual_fii < 0.25:
        return 0.00

    if percentual_fii >= 0.25 and percentual_fii < 0.40:
        return 0.015

    if percentual_fii >= 0.40 and percentual_fii < 0.60:
        return 0.025

    if percentual_fii >= 0.60 and percentual_fii < 0.75:
        return 0.035

    if percentual_fii >= 0.75 and percentual_fii <= 1.00:
        return 0.05

    return math.nan


def classificar_ipca(fii, tipo_fundo, percentual_ativo_fii):
    # sobrescrita manual
    if fii in ipca_por_fii:
        return ipca_por_fii[fii]

    tipo = str(tipo_fundo).lower()

    # Tijolo
    if "tijolo" in tipo:
        return 0.00

    # Papel ou Outro: tratar Outro inicialmente como papel
    if "papel" in tipo or "outro" in tipo:
        return ipca_por_percentual_fii(percentual_ativo_fii)

    # Fallback: se houver percentual de FII, aplica a regra
    if not pd.isna(percentual_ativo_fii):
        return ipca_por_percentual_fii(percentual_ativo_fii)

    return math.nan


def coletar_fii(page, fii):
    url = f"https://investidor10.com.br/fiis/{fii}/"

    page.goto(
        url,
        wait_until="networkidle",
        timeout=60000
    )

    page.wait_for_timeout(3000)

    limpar_tela(page)

    texto = page.locator("body").inner_text()

    p_vp = extrair_valor_por_rotulo(
        texto,
        ["P/VP", "P VP", "PVP"]
    )

    preco = extrair_valor_por_rotulo(
        texto,
        ["Cotação", "Valor atual", "Preço atual"]
    )

    dy_12m = extrair_valor_por_rotulo(
        texto,
        [
            "Dividend Yield 12M",
            "Dividend Yield",
            "DY 12M",
            "Dividendos 12M"
        ]
    )

    tipo_fundo = extrair_tipo_fundo(texto)

    percentual_ativo_fii = extrair_percentual_ativo_fii(page)

    ipca = classificar_ipca(
        fii=fii,
        tipo_fundo=tipo_fundo,
        percentual_ativo_fii=percentual_ativo_fii
    )

    return {
        "FII": fii,
        "P/VP": br_to_float(p_vp),
        "PREÇO": br_to_float(preco),
        "DIVIDENDO 12M %": percent_to_decimal(dy_12m),
        "IPCA": ipca,
        "IPCA+": ipca_mais,
        "PRÊMIO": premio_por_fii.get(fii, 0.01),
    }


dados = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)

    page = browser.new_page(
        user_agent=(
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 Chrome/120 Safari/537.36"
        )
    )

    for fii in fiis:
        try:
            print(f"Coletando {fii}...")
            dados.append(coletar_fii(page, fii))

        except Exception as e:
            print(f"Erro em {fii}: {e}")

            dados.append({
                "FII": fii,
                "P/VP": math.nan,
                "PREÇO": math.nan,
                "DIVIDENDO 12M %": math.nan,
                "IPCA": ipca_por_fii.get(fii, math.nan),
                "IPCA+": ipca_mais,
                "PRÊMIO": premio_por_fii.get(fii, 0.01),
            })

        time.sleep(pausa)

    browser.close()


df = pd.DataFrame(dados)

df["DIVIDENDO 12M (R$)"] = (
    df["PREÇO"]
    * df["DIVIDENDO 12M %"]
)

df["TAXA REQUERIDA"] = (
    df["IPCA+"]
    + df["PRÊMIO"]
)

df["PREÇO TETO"] = (
    df["DIVIDENDO 12M (R$)"]
    / df["TAXA REQUERIDA"]
)

df["MARGEM DE SEG."] = (
    (df["PREÇO TETO"] - df["PREÇO"])
    / df["PREÇO"]
)

df = df[
    [
        "FII",
        "P/VP",
        "PREÇO",
        "DIVIDENDO 12M %",
        "DIVIDENDO 12M (R$)",
        "IPCA",
        "IPCA+",
        "PRÊMIO",
        "PREÇO TETO",
        "MARGEM DE SEG.",
    ]
]

df = df.sort_values(
    by="MARGEM DE SEG.",
    ascending=False
).reset_index(drop=True)

print(df)

df.to_excel("preco_teto_fiis.xlsx", index=False)

print("\nArquivo salvo: preco_teto_fiis.xlsx")