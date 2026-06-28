"""
Dashboard de Análise de FIIs
Disciplina: Estatística — 3ª VA
Dados coletados em tempo real do Investidor10.com.br via Playwright (headless).
"""

import math
import re

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from playwright.sync_api import sync_playwright

# ─────────────────────────────────────────────────────────────────────────────
# Constantes
# ─────────────────────────────────────────────────────────────────────────────

IPCA_MAIS = 0.07  # IPCA+ fixo em 7% conforme enunciado

LISTA_FIIS = sorted([
    "BCFF11", "BPFF11", "BRCR11", "BRCO11", "BTCI11", "BTLG11",
    "CPTS11", "CVBI11", "FAMB11", "GARE11", "GGRC11", "GTWR11",
    "HGLG11", "HSLG11", "HSML11", "IRDM11", "JSRE11", "KNRI11",
    "KNCR11", "LVBI11", "MALL11", "MGFF11", "MXRF11", "PORD11",
    "PVBI11", "RBVA11", "RBRR11", "RCRB11", "RECT11", "RECR11",
    "RZTR11", "SDIL11", "SNAG11", "TGAR11", "TRXF11", "URPR11",
    "VGHF11", "VISC11", "VINO11", "VRTA11", "XPML11",
])

# ─────────────────────────────────────────────────────────────────────────────
# Funções auxiliares de conversão (adaptadas do fiis.py de referência)
# ─────────────────────────────────────────────────────────────────────────────

def br_to_float(valor):
    """Converte string no formato brasileiro (ex: 'R$ 1.234,56' ou '12,5%') para float."""
    if valor is None:
        return math.nan
    txt = str(valor).strip().replace("R$", "").replace("%", "").strip()
    if txt in ["", "-", "N/A", "NaN"]:
        return math.nan
    txt = txt.replace(".", "").replace(",", ".")
    try:
        return float(txt)
    except ValueError:
        return math.nan


def percent_to_decimal(valor):
    """Converte percentual string ('12,5%') para decimal (0.125)."""
    x = br_to_float(valor)
    return math.nan if math.isnan(x) else x / 100


def fmt_brl(v):
    """Formata número como moeda BRL com separadores brasileiros."""
    if math.isnan(v):
        return "—"
    # Converte separadores: 1,234.56 → 1.234,56
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def fmt_pct(v, decimais=2):
    """Formata float como percentual."""
    if math.isnan(v):
        return "—"
    return f"{v:.{decimais}f}%"


# ─────────────────────────────────────────────────────────────────────────────
# Funções de web scraping (Playwright)
# ─────────────────────────────────────────────────────────────────────────────

def _limpar_tela(page):
    """Remove banners e modais que bloqueiam o conteúdo da página."""
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
    except Exception:
        pass
    try:
        page.evaluate("""() => {
            const b = document.querySelector('#guest-user-banner-irpf');
            if (b) b.remove();
            const bd = document.querySelector('.modal-backdrop');
            if (bd) bd.remove();
            document.body.classList.remove('modal-open');
            document.body.style.overflow = 'auto';
            document.body.style.paddingRight = '0px';
        }""")
    except Exception:
        pass


def _extrair_valor_por_rotulo(texto, rotulos):
    """Usa regex para encontrar um valor numérico imediatamente após um rótulo no texto."""
    texto_limpo = re.sub(r"\s+", " ", texto)
    for rotulo in rotulos:
        padrao = rf"{rotulo}\s*[:\-]?\s*(R\$)?\s*(-?[\d\.\,]+%?)"
        m = re.search(padrao, texto_limpo, flags=re.IGNORECASE)
        if m:
            return m.group(2)
    return None


def _extrair_tipo_fundo(texto):
    """Extrai o tipo do fundo ('tijolo', 'papel', etc.) do texto da página."""
    texto_limpo = re.sub(r"\s+", " ", texto)
    for padrao in [
        r"Tipo de fundo\s*[:\-]?\s*([A-Za-zÀ-ÿ\s]+)",
        r"Tipo\s*[:\-]?\s*([A-Za-zÀ-ÿ\s]+)",
    ]:
        m = re.search(padrao, texto_limpo, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip().lower()
    return ""


def _extrair_percentual_ativo_fii(page):
    """Extrai o % de ativos classificados como FII (para calcular IPCA de fundos híbridos)."""
    try:
        valor = page.evaluate("""() => {
            const nomes = Array.from(document.querySelectorAll('.legend-name'));
            const vals  = Array.from(document.querySelectorAll('.legend-value'));
            for (let i = 0; i < nomes.length; i++) {
                if (nomes[i].innerText.trim().toUpperCase() === 'FII') {
                    return vals[i] ? vals[i].innerText.trim() : null;
                }
            }
            return null;
        }""")
        # Se não encontrar, assume 100% (fundo de papel puro → IPCA = 5%)
        return 1.00 if valor is None else percent_to_decimal(valor)
    except Exception:
        return 1.00


def _ipca_por_percentual_fii(pct):
    """
    Tabela de IPCA baseada no percentual de ativos FII.
    Quanto maior o percentual de ativos reais, menor o IPCA aplicado.
    """
    if math.isnan(pct):
        return math.nan
    if pct < 0.25:
        return 0.00
    if pct < 0.40:
        return 0.015
    if pct < 0.60:
        return 0.025
    if pct < 0.75:
        return 0.035
    return 0.05


def _classificar_ipca(tipo_fundo, percentual_ativo_fii):
    """
    Define IPCA do FII conforme enunciado:
      - Tijolo: IPCA = 0%
      - Papel: IPCA = 5% (ou baseado no % de FII para fundos híbridos)
    """
    tipo = str(tipo_fundo).lower()
    if "tijolo" in tipo:
        return 0.00
    if "papel" in tipo or "outro" in tipo:
        return _ipca_por_percentual_fii(percentual_ativo_fii)
    if not math.isnan(percentual_ativo_fii):
        return _ipca_por_percentual_fii(percentual_ativo_fii)
    return 0.05  # fallback conservador


@st.cache_data(ttl=3600, show_spinner="Buscando dados no Investidor10…")
def fetch_fii_data(ticker: str) -> dict:
    """
    Raspa cotação atual, DY 12M e P/VP do Investidor10 via Playwright headless.
    Resultado é cacheado por 1 hora para evitar requisições repetidas.
    """
    ticker = ticker.upper().strip()
    url = f"https://investidor10.com.br/fiis/{ticker}/"

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 Chrome/120 Safari/537.36"
            )
        )
        try:
            # Aguarda a página carregar completamente antes de extrair dados
            page.goto(url, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(3000)
            _limpar_tela(page)

            texto = page.locator("body").inner_text()

            p_vp    = _extrair_valor_por_rotulo(texto, ["P/VP", "P VP", "PVP"])
            preco   = _extrair_valor_por_rotulo(texto, ["Cotação", "Valor atual", "Preço atual"])
            dy_12m  = _extrair_valor_por_rotulo(
                texto,
                ["Dividend Yield 12M", "Dividend Yield", "DY 12M", "Dividendos 12M"],
            )
            tipo       = _extrair_tipo_fundo(texto)
            pct_fii    = _extrair_percentual_ativo_fii(page)
            ipca       = _classificar_ipca(tipo, pct_fii)

            resultado = {
                "FII":             ticker,
                "PREÇO":           br_to_float(preco),
                "DIVIDENDO 12M %": percent_to_decimal(dy_12m),
                "P/VP":            br_to_float(p_vp),
                "IPCA":            ipca,
                "IPCA+":           IPCA_MAIS,
            }
        except Exception as e:
            resultado = {
                "FII":             ticker,
                "PREÇO":           math.nan,
                "DIVIDENDO 12M %": math.nan,
                "P/VP":            math.nan,
                "IPCA":            math.nan,
                "IPCA+":           IPCA_MAIS,
                "_erro":           str(e),
            }
        finally:
            browser.close()

    return resultado


# ─────────────────────────────────────────────────────────────────────────────
# Configuração da página
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Dashboard FIIs",
    page_icon="🏢",
    layout="wide",
)

st.title("🏢 Dashboard de Análise de FIIs")
st.caption("Dados coletados em tempo real do Investidor10.com.br")

tab1, tab2, tab3 = st.tabs([
    "📈 Simulação de Aporte Mensal",
    "💼 Carteira de FIIs",
    "🎯 Preço Teto",
])

# ─────────────────────────────────────────────────────────────────────────────
# ABA 1 — Simulação de Aporte Mensal
# ─────────────────────────────────────────────────────────────────────────────

with tab1:
    st.header("Simulação de Aporte Mensal")
    st.markdown(
        "Informe o FII, quantas cotas comprar por mês e por quantos meses "
        "para ver a projeção de patrimônio e renda."
    )

    c1, c2, c3 = st.columns(3)
    ticker_sim = c1.selectbox(
        "Ticker do FII", options=LISTA_FIIS,
        index=LISTA_FIIS.index("MXRF11"), key="sim_ticker"
    )
    qtd_mensal = int(c2.number_input(
        "Cotas compradas por mês", min_value=1, value=10, step=1, key="sim_qtd"
    ))
    meses = int(c3.number_input(
        "Meses de projeção", min_value=1, max_value=360, value=120, step=12, key="sim_meses"
    ))

    if st.button("▶ Simular", type="primary", key="btn_sim"):
        if not ticker_sim:
            st.warning("Informe o ticker do FII.")
        else:
            dados = fetch_fii_data(ticker_sim)

            if math.isnan(dados["PREÇO"]):
                st.error(
                    f"Não foi possível obter dados para **{ticker_sim}**. "
                    "Verifique o ticker e tente novamente."
                )
            else:
                preco        = dados["PREÇO"]
                dy_12m       = dados["DIVIDENDO 12M %"]
                # Dividendo mensal estimado por cota = (Preço × DY anual) / 12
                div_mes_cota = (preco * dy_12m) / 12

                # Métricas de resumo
                m1, m2, m3 = st.columns(3)
                m1.metric("Cotação Atual",         fmt_brl(preco))
                m2.metric("DY 12M",                fmt_pct(dy_12m * 100))
                m3.metric("Dividendo Mensal/cota", fmt_brl(div_mes_cota))

                # Projeção mês a mês
                rows = []
                cotas_acum = total_inv = renda_acum = 0.0

                for mes in range(1, meses + 1):
                    cotas_acum += qtd_mensal
                    inv_mes     = preco * qtd_mensal          # aporte do mês
                    total_inv  += inv_mes
                    renda_mes   = div_mes_cota * cotas_acum   # renda do mês com todas as cotas
                    renda_acum += renda_mes

                    rows.append({
                        "Mês":              mes,
                        "Inv. Mensal":      inv_mes,
                        "Cotas Acum.":      int(cotas_acum),
                        "Total Investido":  total_inv,
                        "Renda Mensal":     renda_mes,
                        "Renda Acumulada":  renda_acum,
                    })

                df_sim = pd.DataFrame(rows)

                # Gráfico de evolução patrimonial
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_sim["Mês"], y=df_sim["Total Investido"],
                    name="Total Investido",
                    line=dict(color="#1f77b4", width=2),
                ))
                fig.add_trace(go.Scatter(
                    x=df_sim["Mês"], y=df_sim["Renda Acumulada"],
                    name="Renda Acumulada",
                    line=dict(color="#2ca02c", width=2),
                ))
                fig.update_layout(
                    title=f"Projeção de {meses} meses — {ticker_sim}",
                    xaxis_title="Mês",
                    yaxis_title="R$",
                    hovermode="x unified",
                    legend=dict(orientation="h", y=1.1),
                )
                st.plotly_chart(fig, use_container_width=True)

                # Tabela formatada
                st.subheader("Tabela de Projeção")
                df_exib = df_sim.copy()
                for col in ["Inv. Mensal", "Total Investido", "Renda Mensal", "Renda Acumulada"]:
                    df_exib[col] = df_exib[col].apply(fmt_brl)
                st.dataframe(df_exib, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────────────────────────────────────
# ABA 2 — Carteira com Múltiplos FIIs
# ─────────────────────────────────────────────────────────────────────────────

with tab2:
    st.header("Carteira com Múltiplos FIIs")
    st.markdown("Monte uma carteira de 4 a 10 FIIs e visualize investimento e renda mensal.")

    n_fiis = st.selectbox(
        "Número de FIIs na carteira", options=list(range(4, 11)), index=1, key="n_fiis"
    )

    tickers_cart, qtds_cart = [], []
    for i in range(n_fiis):
        c1, c2 = st.columns([2, 1])
        tickers_cart.append(
            c1.selectbox(f"Ticker {i + 1}", options=LISTA_FIIS, index=i % len(LISTA_FIIS), key=f"ct_{i}")
        )
        qtds_cart.append(int(
            c2.number_input(f"Quantidade {i + 1}", min_value=0, value=100, step=10, key=f"cq_{i}")
        ))

    if st.button("▶ Calcular Carteira", type="primary", key="btn_cart"):
        pares = [(t, q) for t, q in zip(tickers_cart, qtds_cart) if t and q > 0]

        if len(pares) < 2:
            st.warning("Informe ao menos 2 FIIs com quantidade maior que zero.")
        else:
            linhas, erros = [], []
            prog = st.progress(0)

            for idx, (t, q) in enumerate(pares):
                prog.progress((idx + 1) / len(pares), text=f"Buscando {t}…")
                d = fetch_fii_data(t)

                if math.isnan(d["PREÇO"]):
                    erros.append(t)
                    continue

                preco = d["PREÇO"]
                dy    = d["DIVIDENDO 12M %"]
                inv   = preco * q
                # Proventos por cota = dividendo mensal estimado
                prov  = (preco * dy) / 12
                renda = prov * q

                linhas.append({
                    "FII":             t,
                    "Preço":           preco,
                    "Quantidade":      q,
                    "Investimento":    inv,
                    "Proventos/cota":  prov,
                    "Renda Mensal":    renda,
                    "DY 12M %":        dy * 100,
                })

            prog.empty()

            if erros:
                st.warning(f"Sem dados para: {', '.join(erros)}")

            if linhas:
                df_c = pd.DataFrame(linhas)

                total_inv   = df_c["Investimento"].sum()
                total_renda = df_c["Renda Mensal"].sum()
                # DY médio ponderado pelo valor investido em cada FII
                dy_medio    = (df_c["DY 12M %"] * df_c["Investimento"]).sum() / total_inv

                m1, m2, m3 = st.columns(3)
                m1.metric("Total Investido",    fmt_brl(total_inv))
                m2.metric("Renda Mensal Total", fmt_brl(total_renda))
                m3.metric("DY Médio Ponderado", fmt_pct(dy_medio))

                # Gráfico de pizza — alocação por FII
                fig_p = px.pie(
                    df_c, names="FII", values="Investimento",
                    title="Alocação da Carteira por FII",
                    hole=0.35,
                )
                st.plotly_chart(fig_p, use_container_width=True)

                # Tabela formatada
                df_exib = df_c.copy()
                for col in ["Preço", "Investimento", "Proventos/cota", "Renda Mensal"]:
                    df_exib[col] = df_exib[col].apply(fmt_brl)
                df_exib["DY 12M %"] = df_exib["DY 12M %"].apply(fmt_pct)
                st.dataframe(df_exib, use_container_width=True, hide_index=True)

                # Persiste os tickers na sessão para uso na Aba 3
                st.session_state["tickers_carteira"] = [r["FII"] for r in linhas]
                st.success("Carteira calculada! Você pode usá-la na aba 🎯 Preço Teto.")

# ─────────────────────────────────────────────────────────────────────────────
# ABA 3 — Preço Teto
# ─────────────────────────────────────────────────────────────────────────────

with tab3:
    st.header("Cálculo de Preço Teto")
    st.markdown("""
**Fórmulas utilizadas (conforme enunciado):**

> `Div 12M (R$) = Preço × DY 12M%`
>
> `Taxa Requerida = IPCA + IPCA+ (7%) + Prêmio`
>
> `Preço Teto = Div 12M (R$) ÷ Taxa Requerida`
>
> `Margem de Segurança = (Preço Teto − Preço Atual) ÷ Preço Atual`

| Prêmio de Risco | Critério |
|---|---|
| **1% — Baixo** | FII grande, patrimônio > R$ 2 bi, DY ≤ 12% |
| **3% — Médio**  | FII médio, papel ou tijolo, DY até 16% |
| **5% — Alto**   | Demais casos |
    """)

    st.divider()

    # Origem dos tickers: carteira da Aba 2 ou entrada manual
    tickers_salvo = st.session_state.get("tickers_carteira", [])
    usar_cart = False

    if tickers_salvo:
        usar_cart = st.checkbox(
            f"Usar tickers da carteira ({', '.join(tickers_salvo)})",
            value=True,
            key="teto_usar_cart",
        )

    if usar_cart and tickers_salvo:
        tickers_teto = tickers_salvo
        st.info(f"Usando: **{', '.join(tickers_teto)}**")
    else:
        tickers_teto = st.multiselect(
            "Selecione os FIIs",
            options=LISTA_FIIS,
            default=["MXRF11", "KNCR11", "HGLG11", "XPML11", "BTLG11"],
            key="teto_raw",
        )

    # Seleção de prêmio de risco por FII
    mapa_premio = {"Baixo (1%)": 0.01, "Médio (3%)": 0.03, "Alto (5%)": 0.05}
    premios: dict[str, float] = {}

    if tickers_teto:
        st.subheader("Prêmio de Risco por FII")
        colunas = st.columns(min(len(tickers_teto), 5))
        for i, t in enumerate(tickers_teto):
            with colunas[i % 5]:
                opcao = st.selectbox(t, list(mapa_premio.keys()), index=1, key=f"p_{t}")
                premios[t] = mapa_premio[opcao]

    if st.button("▶ Calcular Preço Teto", type="primary", key="btn_teto"):
        if not tickers_teto:
            st.warning("Informe ao menos um ticker.")
        else:
            linhas_t, erros_t = [], []
            prog2 = st.progress(0)

            for idx, t in enumerate(tickers_teto):
                prog2.progress((idx + 1) / len(tickers_teto), text=f"Processando {t}…")
                d = fetch_fii_data(t)

                if math.isnan(d["PREÇO"]):
                    erros_t.append(t)
                    continue

                preco   = d["PREÇO"]
                dy_pct  = d["DIVIDENDO 12M %"]
                p_vp    = d["P/VP"]
                ipca    = d["IPCA"]
                ip_mais = d["IPCA+"]
                premio  = premios.get(t, 0.03)

                # Cálculo do preço teto conforme fórmula do enunciado
                div_rs  = preco * dy_pct
                taxa    = ipca + ip_mais + premio        # IPCA + IPCA+ + Prêmio
                teto    = div_rs / taxa if taxa > 0 else math.nan
                margem  = (teto - preco) / preco if (not math.isnan(teto) and preco > 0) else math.nan

                linhas_t.append({
                    "FII":             t,
                    "P/VP":            p_vp,
                    "Preço (R$)":      preco,
                    "Div 12M %":       dy_pct * 100,
                    "Div 12M (R$)":    div_rs,
                    "IPCA (%)":        ipca * 100,
                    "IPCA+ (%)":       ip_mais * 100,
                    "Prêmio (%)":      premio * 100,
                    "Preço Teto (R$)": teto,
                    "Margem Seg. (%)": margem * 100,
                })

            prog2.empty()

            if erros_t:
                st.warning(f"Sem dados para: {', '.join(erros_t)}")

            if linhas_t:
                df_t = pd.DataFrame(linhas_t)

                # Gráfico de barras — Margem de Segurança por FII
                df_sort = df_t.sort_values("Margem Seg. (%)")
                fig_b = go.Figure(go.Bar(
                    x=df_sort["Margem Seg. (%)"],
                    y=df_sort["FII"],
                    orientation="h",
                    marker_color=[
                        "#2ca02c" if v >= 0 else "#d62728"
                        for v in df_sort["Margem Seg. (%)"]
                    ],
                    text=[f"{v:.1f}%" for v in df_sort["Margem Seg. (%)"]],
                    textposition="outside",
                ))
                fig_b.add_vline(x=0, line_dash="dash", line_color="gray")
                fig_b.update_layout(
                    title="Margem de Segurança por FII",
                    xaxis_title="Margem de Segurança (%)",
                    yaxis_title="",
                    xaxis=dict(ticksuffix="%"),
                )
                st.plotly_chart(fig_b, use_container_width=True)

                # Tabela com destaque de cor na coluna Margem de Segurança
                def _cor_margem(col):
                    return [
                        "background-color: #c8f7c5" if v >= 0 else "background-color: #f7c5c5"
                        for v in col
                    ]

                styled = (
                    df_t.style
                    .apply(_cor_margem, subset=["Margem Seg. (%)"])
                    .format({
                        "P/VP":             "{:.2f}",
                        "Preço (R$)":       "R$ {:.2f}",
                        "Div 12M %":        "{:.2f}%",
                        "Div 12M (R$)":     "R$ {:.4f}",
                        "IPCA (%)":         "{:.1f}%",
                        "IPCA+ (%)":        "{:.1f}%",
                        "Prêmio (%)":       "{:.0f}%",
                        "Preço Teto (R$)":  "R$ {:.2f}",
                        "Margem Seg. (%)":  "{:.2f}%",
                    }, na_rep="—")
                )
                st.dataframe(styled, use_container_width=True, hide_index=True)
