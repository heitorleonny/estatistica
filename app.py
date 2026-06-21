from shiny import App, Inputs, Outputs, Session, reactive, render, req, ui
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

# ─────────────────────────── UI ────────────────────────────
# Os selects de variável são renderizados dinamicamente no server
# (ui.output_ui) para garantir que as choices se atualizem ao
# carregar um arquivo, sem depender de ui.update_select.

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.h5("Carregar Dados"),
        ui.input_file(
            "file_upload",
            "Selecione CSV ou Excel:",
            accept=[".csv", ".xlsx", ".xls"],
            multiple=False,
            button_label="Escolher arquivo",
            placeholder="Nenhum arquivo selecionado",
        ),
        ui.hr(),
        ui.output_text_verbatim("file_status", placeholder=True),
        width=300,
        open="always",
    ),
    ui.navset_card_tab(
        # ── Tab 1: Análise Descritiva ──────────────────────
        ui.nav_panel(
            "1. Análise Descritiva",
            ui.layout_columns(
                ui.card(
                    ui.card_header("Variável"),
                    ui.output_ui("desc_var_ui"),
                ),
                col_widths=[12],
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Histograma"),
                    ui.output_plot("desc_hist"),
                ),
                ui.card(
                    ui.card_header("Boxplot"),
                    ui.output_plot("desc_box"),
                ),
                col_widths=[6, 6],
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Estatísticas Descritivas"),
                    ui.output_table("desc_stats"),
                ),
                col_widths=[12],
            ),
        ),
        # ── Tab 2: Teste de Hipóteses ──────────────────────
        ui.nav_panel(
            "2. Teste de Hipóteses",
            ui.layout_columns(
                ui.card(
                    ui.card_header("Parâmetros do Teste"),
                    ui.output_ui("hyp_var_ui"),
                    ui.input_numeric(
                        "hyp_sigma2",
                        "Variância populacional (σ²):",
                        value=1.0,
                        min=0.0001,
                        step=0.1,
                    ),
                    ui.input_radio_buttons(
                        "hyp_type",
                        "Tipo de teste:",
                        choices={
                            "bilateral": "Bilateral  (H₁: μ ≠ μ₀)",
                            "direita":   "Unilateral à direita  (H₁: μ > μ₀)",
                            "esquerda":  "Unilateral à esquerda  (H₁: μ < μ₀)",
                        },
                        selected="bilateral",
                    ),
                    ui.input_slider("hyp_mu0", "Valor de μ₀:", min=-1000, max=1000, value=0, step=0.5),
                    ui.input_slider("hyp_alpha", "Nível de significância (α):", min=0.01, max=0.20, value=0.05, step=0.01),
                ),
                ui.card(
                    ui.card_header("Resultados"),
                    ui.output_text_verbatim("hyp_results"),
                    ui.card_header("Distribuição Normal — Região Crítica"),
                    ui.output_plot("hyp_plot"),
                ),
                col_widths=[5, 7],
            ),
        ),
        # ── Tab 3: Intervalo de Confiança ──────────────────
        ui.nav_panel(
            "3. Intervalo de Confiança Normal",
            ui.layout_columns(
                ui.card(
                    ui.card_header("Parâmetros"),
                    ui.output_ui("ci_var_ui"),
                    ui.input_numeric("ci_sigma2", "Variância populacional (σ²):", value=1.0, min=0.0001, step=0.1),
                    ui.input_slider("ci_level", "Nível de confiança (1 − α):", min=0.80, max=0.99, value=0.95, step=0.01),
                ),
                ui.card(
                    ui.card_header("Resultado"),
                    ui.output_text_verbatim("ci_results"),
                ),
                col_widths=[5, 7],
            ),
        ),
        # ── Tab 4: Regressão Linear Simples ────────────────
        ui.nav_panel(
            "4. Regressão Linear Simples",
            ui.layout_columns(
                ui.card(
                    ui.card_header("Variáveis"),
                    ui.output_ui("reg_y_ui"),
                    ui.output_ui("reg_x_ui"),
                ),
                ui.card(
                    ui.card_header("Resultados"),
                    ui.output_text_verbatim("reg_results"),
                ),
                col_widths=[4, 8],
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Dispersão e Reta de Regressão"),
                    ui.output_plot("reg_plot"),
                ),
                col_widths=[12],
            ),
        ),
        id="tabs",
    ),
    title="Dashboard Estatístico",
)

# ─────────────────────────── SERVER ────────────────────────

def server(input: Inputs, output: Outputs, session: Session):

    # ── Carregamento e detecção de colunas ──────────────────

    @reactive.calc
    def parsed_data():
        file_info = input.file_upload()
        if file_info is None:
            return None
        path = file_info[0]["datapath"]
        name = file_info[0]["name"].lower()
        try:
            if name.endswith(".csv"):
                df = pd.read_csv(path)
            elif name.endswith(".xlsx"):
                df = pd.read_excel(path, engine="openpyxl")
            elif name.endswith(".xls"):
                df = pd.read_excel(path, engine="xlrd")
            else:
                return None
            return df
        except Exception:
            return None

    @reactive.calc
    def numeric_cols():
        df = parsed_data()
        if df is None:
            return []
        result = []
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                result.append(col)
            else:
                # tenta converter (captura colunas como "5.0" em texto)
                converted = pd.to_numeric(df[col], errors="coerce")
                if converted.notna().mean() >= 0.5:
                    result.append(col)
        return result

    # ── Status do arquivo ────────────────────────────────────

    @render.text
    def file_status():
        df = parsed_data()
        if df is None:
            info = input.file_upload()
            if info is None:
                return "Nenhum arquivo carregado."
            return "Erro ao ler o arquivo.\nVerifique se é CSV ou Excel válido."
        n_rows, n_cols = df.shape
        nc = len(numeric_cols())
        return (
            f"✓ {input.file_upload()[0]['name']}\n"
            f"Linhas    : {n_rows}\n"
            f"Colunas   : {n_cols}\n"
            f"Numéricas : {nc}"
        )

    # ── Selects dinâmicos (renderizados pelo server) ─────────

    def _make_select(input_id, label, second=False):
        cols = numeric_cols()
        if not cols:
            return ui.p("Carregue um arquivo com colunas numéricas.", style="color:gray;font-style:italic;")
        selected = cols[1] if second and len(cols) > 1 else cols[0]
        return ui.input_select(input_id, label, choices=cols, selected=selected)

    @render.ui
    def desc_var_ui():
        return _make_select("desc_var", "Variável numérica:")

    @render.ui
    def hyp_var_ui():
        return _make_select("hyp_var", "Variável numérica:")

    @render.ui
    def ci_var_ui():
        return _make_select("ci_var", "Variável numérica:")

    @render.ui
    def reg_y_ui():
        return _make_select("reg_y", "Variável resposta (Y):")

    @render.ui
    def reg_x_ui():
        return _make_select("reg_x", "Variável explicativa (X):", second=True)

    # ── Helpers ──────────────────────────────────────────────

    def _get_series(input_id):
        df = parsed_data()
        if df is None:
            return None
        try:
            var = getattr(input, input_id)()
        except Exception:
            return None
        if not var or var not in df.columns:
            return None
        series = pd.to_numeric(df[var], errors="coerce").dropna()
        return series if len(series) > 0 else None

    # ── Tab 1: Análise Descritiva ────────────────────────────

    @render.plot
    def desc_hist():
        series = _get_series("desc_var")
        if series is None:
            return
        try:
            var = input.desc_var()
        except Exception:
            return
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.hist(series, bins="auto", color="steelblue", edgecolor="white", alpha=0.85)
        ax.set_xlabel(var)
        ax.set_ylabel("Frequência")
        ax.set_title(f"Histograma — {var}")
        ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout()
        return fig

    @render.plot
    def desc_box():
        series = _get_series("desc_var")
        if series is None:
            return
        try:
            var = input.desc_var()
        except Exception:
            return
        fig, ax = plt.subplots(figsize=(4, 5))
        ax.boxplot(
            series,
            patch_artist=True,
            boxprops=dict(facecolor="steelblue", color="navy"),
            medianprops=dict(color="white", linewidth=2),
            whiskerprops=dict(color="navy"),
            capprops=dict(color="navy"),
            flierprops=dict(marker="o", color="steelblue", alpha=0.5),
        )
        ax.set_ylabel(var)
        ax.set_title(f"Boxplot — {var}")
        ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout()
        return fig

    @render.table
    def desc_stats():
        series = _get_series("desc_var")
        if series is None:
            return pd.DataFrame()
        return pd.DataFrame({
            "Estatística": ["Média", "Mediana", "Desvio Padrão", "Tamanho (n)", "Mínimo", "Máximo"],
            "Valor": [
                f"{series.mean():.4f}",
                f"{series.median():.4f}",
                f"{series.std(ddof=1):.4f}",
                f"{len(series)}",
                f"{series.min():.4f}",
                f"{series.max():.4f}",
            ],
        })

    # ── Tab 2: Teste de Hipóteses (Z-test) ──────────────────

    def _hyp_compute():
        series = _get_series("hyp_var")
        if series is None:
            return None
        sigma2 = input.hyp_sigma2()
        if sigma2 is None or sigma2 <= 0:
            return None
        mu0       = input.hyp_mu0()
        alpha     = input.hyp_alpha()
        test_type = input.hyp_type()
        n     = len(series)
        x_bar = series.mean()
        se    = np.sqrt(sigma2) / np.sqrt(n)
        Z     = (x_bar - mu0) / se
        if test_type == "bilateral":
            p_value = 2 * (1 - stats.norm.cdf(abs(Z)))
            z_crit  = stats.norm.ppf(1 - alpha / 2)
            reject  = abs(Z) > z_crit
        elif test_type == "direita":
            p_value = 1 - stats.norm.cdf(Z)
            z_crit  = stats.norm.ppf(1 - alpha)
            reject  = Z > z_crit
        else:
            p_value = stats.norm.cdf(Z)
            z_crit  = stats.norm.ppf(alpha)
            reject  = Z < z_crit
        return dict(n=n, x_bar=x_bar, sigma2=sigma2, mu0=mu0, alpha=alpha,
                    test_type=test_type, Z=Z, p_value=p_value, z_crit=z_crit, reject=reject)

    @render.text
    def hyp_results():
        r = _hyp_compute()
        if r is None:
            return "Carregue um arquivo, selecione uma variável e informe σ² > 0."
        h1 = {"bilateral": f"μ ≠ {r['mu0']}", "direita": f"μ > {r['mu0']}", "esquerda": f"μ < {r['mu0']}"}
        decision = "*** Rejeitar H₀ ***" if r["reject"] else "Não rejeitar H₀"
        return (
            f"H₀: μ = {r['mu0']}\n"
            f"H₁: {h1[r['test_type']]}\n"
            f"─────────────────────────\n"
            f"n           = {r['n']}\n"
            f"x̄           = {r['x_bar']:.4f}\n"
            f"σ²          = {r['sigma2']}\n"
            f"α           = {r['alpha']:.2f}\n"
            f"─────────────────────────\n"
            f"Z calculado = {r['Z']:.4f}\n"
            f"Z crítico   = {abs(r['z_crit']):.4f}\n"
            f"p-valor     = {r['p_value']:.4f}\n"
            f"─────────────────────────\n"
            f"Decisão: {decision}"
        )

    @render.plot
    def hyp_plot():
        r = _hyp_compute()
        if r is None:
            return
        x  = np.linspace(-4, 4, 500)
        y  = stats.norm.pdf(x)
        zc = abs(r["z_crit"])
        fig, ax = plt.subplots(figsize=(6, 3.5))
        ax.plot(x, y, color="navy", linewidth=2)
        ax.fill_between(x, y, color="lightsteelblue", alpha=0.25)
        if r["test_type"] == "bilateral":
            ax.fill_between(x, y, where=(x >=  zc), color="tomato", alpha=0.55, label="Região crítica")
            ax.fill_between(x, y, where=(x <= -zc), color="tomato", alpha=0.55)
            ax.axvline( zc, color="red", linestyle="--", linewidth=1.2)
            ax.axvline(-zc, color="red", linestyle="--", linewidth=1.2)
        elif r["test_type"] == "direita":
            ax.fill_between(x, y, where=(x >= zc), color="tomato", alpha=0.55, label="Região crítica")
            ax.axvline(zc, color="red", linestyle="--", linewidth=1.2)
        else:
            ax.fill_between(x, y, where=(x <= -zc), color="tomato", alpha=0.55, label="Região crítica")
            ax.axvline(-zc, color="red", linestyle="--", linewidth=1.2)
        z_vis = max(-4.2, min(4.2, r["Z"]))
        ax.axvline(z_vis, color="darkgreen", linewidth=2.2, label=f"Z = {r['Z']:.3f}")
        ax.set_xlabel("Z")
        ax.set_ylabel("Densidade")
        ax.set_title("Distribuição Normal Padrão")
        ax.legend(fontsize=8)
        ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout()
        return fig

    # ── Tab 3: Intervalo de Confiança ───────────────────────

    @render.text
    def ci_results():
        series = _get_series("ci_var")
        if series is None:
            return "Carregue um arquivo e selecione uma variável."
        sigma2 = input.ci_sigma2()
        if sigma2 is None or sigma2 <= 0:
            return "σ² deve ser um valor positivo."
        n      = len(series)
        x_bar  = series.mean()
        level  = input.ci_level()
        alpha  = 1 - level
        se     = np.sqrt(sigma2) / np.sqrt(n)
        z_crit = stats.norm.ppf(1 - alpha / 2)
        lower  = x_bar - z_crit * se
        upper  = x_bar + z_crit * se
        try:
            var = input.ci_var()
        except Exception:
            var = "—"
        return (
            f"Variável : {var}\n"
            f"n        = {n}\n"
            f"x̄        = {x_bar:.4f}\n"
            f"σ²       = {sigma2}\n"
            f"─────────────────────────────────\n"
            f"Nível de confiança = {level * 100:.0f}%\n"
            f"z(α/2)             = {z_crit:.4f}\n"
            f"─────────────────────────────────\n"
            f"Limite inferior = {lower:.4f}\n"
            f"Limite superior = {upper:.4f}\n"
            f"\nIC {level*100:.0f}%: [ {lower:.4f}  ;  {upper:.4f} ]"
        )

    # ── Tab 4: Regressão Linear Simples ─────────────────────

    def _reg_data():
        df = parsed_data()
        if df is None:
            return None
        try:
            y_var = input.reg_y()
            x_var = input.reg_x()
        except Exception:
            return None
        if not y_var or not x_var:
            return None
        if y_var not in df.columns or x_var not in df.columns:
            return None
        if y_var == x_var:
            return None
        sub = pd.DataFrame({
            x_var: pd.to_numeric(df[x_var], errors="coerce"),
            y_var: pd.to_numeric(df[y_var], errors="coerce"),
        }).dropna()
        return (sub, x_var, y_var) if len(sub) >= 3 else None

    @render.text
    def reg_results():
        result = _reg_data()
        if result is None:
            return "Carregue um arquivo e selecione variáveis X e Y diferentes."
        sub, x_var, y_var = result
        x = sub[x_var].values
        y = sub[y_var].values
        slope, intercept, r, p, se = stats.linregress(x, y)
        r2   = r ** 2
        sign = "+" if intercept >= 0 else "-"
        eq   = f"ŷ = {slope:.4f}·x {sign} {abs(intercept):.4f}"
        return (
            f"Y (resposta)       : {y_var}\n"
            f"X (explicativa)    : {x_var}\n"
            f"n                  = {len(x)}\n"
            f"─────────────────────────────────\n"
            f"R (correlação)     = {r:.4f}\n"
            f"R²                 = {r2:.4f}\n"
            f"─────────────────────────────────\n"
            f"Intercepto (β₀)    = {intercept:.4f}\n"
            f"Coef. angular (β₁) = {slope:.4f}\n"
            f"\nEquação: {eq}\n"
            f"\np-valor (β₁)      = {p:.4f}"
        )

    @render.plot
    def reg_plot():
        result = _reg_data()
        if result is None:
            return
        sub, x_var, y_var = result
        x = sub[x_var].values
        y = sub[y_var].values
        slope, intercept, r, _, _ = stats.linregress(x, y)
        x_line = np.linspace(x.min(), x.max(), 300)
        y_line = slope * x_line + intercept
        sign   = "+" if intercept >= 0 else "-"
        label  = f"ŷ = {slope:.3f}·x {sign} {abs(intercept):.3f}  (R²={r**2:.3f})"
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.scatter(x, y, color="steelblue", alpha=0.55, edgecolors="white", s=40, label="Dados")
        ax.plot(x_line, y_line, color="crimson", linewidth=2, label=label)
        ax.set_xlabel(x_var)
        ax.set_ylabel(y_var)
        ax.set_title(f"Regressão Linear: {y_var} ~ {x_var}")
        ax.legend(fontsize=9)
        ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout()
        return fig


app = App(app_ui, server)
