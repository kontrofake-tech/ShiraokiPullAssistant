import streamlit as st
import math

# ==========================================
#              LOGIC & MATH
# ==========================================

def calculate_data(total_pulls, mode_selection, pool_ssr, pool_sr):
    # --- Setup ---
    has_promo_sr = ("1 Promo SR" in mode_selection)
    
    cur_pool_ssr = pool_ssr - (1 if has_promo_sr else 2)
    cur_pool_sr = pool_sr - (1 if has_promo_sr else 0)

    # --- Math Helpers ---
    def nCr(n, r):
        if r < 0 or r > n: return 0
        f = math.factorial
        return f(n) // (f(r) * f(n - r))

    def binom_pmf(k, n, p):
        return nCr(n, k) * (p ** k) * ((1 - p) ** (n - k))

    # --- Rates ---
    if has_promo_sr:
        r_p_ssr, r_o_ssr = 0.0075, 0.0225
        r_p_sr_n, r_p_sr_s = 0.0225, 0.12125
    else:
        r_p_ssr, r_o_ssr = 0.015, 0.015
        r_p_sr_n, r_p_sr_s = 0.0, 0.0

    r_n_sr_pool = 0.18 - r_p_sr_n
    r_s_sr_pool = 0.97 - r_p_sr_s
    
    num_special = total_pulls // 10
    num_normal = total_pulls - num_special

    def get_avg(pn, ps): return ((num_normal * pn) + (num_special * ps)) / total_pulls

    # --- Calculations ---
    data = {}
    
    # Pity
    data['pity_count'] = total_pulls // 200
    data['pity_next'] = 200 - (total_pulls % 200)
    data['pity_cost'] = data['pity_next'] * 150
    
    # Stats (Mean/Sigma)
    ev_ssr = total_pulls * 0.03
    sig_ssr = math.sqrt(total_pulls * 0.03 * 0.97)
    ev_ban = total_pulls * r_p_ssr
    sig_ban = math.sqrt(total_pulls * r_p_ssr * (1 - r_p_ssr))
    var_sr = (num_normal * 0.18 * 0.82) + (num_special * 0.97 * 0.03)
    ev_sr = (num_normal * 0.18) + (num_special * 0.97)
    sig_sr = math.sqrt(var_sr)

    data['stats'] = [
        {'title': 'Total SRs Expected', 'mu': ev_sr, 'sigma': sig_sr, 'color': '#D69E2E', 'bg': '#FFFFF0', 'icon': '✨'},
        {'title': 'Total SSRs Expected', 'mu': ev_ssr, 'sigma': sig_ssr, 'color': '#805AD5', 'bg': '#FAF5FF', 'icon': '🔮'},
        {'title': 'Banner SSRs Expected', 'mu': ev_ban, 'sigma': sig_ban, 'color': '#E53E3E', 'bg': '#FFF5F5', 'icon': '🔥'}
    ]

    # Tables Data Generation
    def gen_table_rows(n, p):
        rows = []
        cum_excl = 0.0
        k = 0
        expected = n * p
        while True:
            prob = binom_pmf(k, n, p)
            plus = max(0.0, 1.0 - cum_excl)
            rows.append((k, prob, plus))
            cum_excl += prob
            if prob < 0.005 and k > expected: break
            k += 1
        rem = max(0.0, 1.0 - cum_excl)
        if rem > 0.0001: rows.append((f"{k+1}+", rem, rem))
        return rows

    p_1_p_sr = get_avg(r_p_sr_n, r_p_sr_s)
    p_1_o_ssr = r_o_ssr / max(1, cur_pool_ssr)
    p_1_o_sr = get_avg(r_n_sr_pool, r_s_sr_pool) / max(1, cur_pool_sr)

    data['tables'] = []
    
    if not has_promo_sr:
        data['tables'].append({'name': 'Total Banner SSRs (Both Cards)', 'rows': gen_table_rows(total_pulls, r_p_ssr), 'color': '#E53E3E', 'bg': '#FFF5F5'})
    
    if has_promo_sr:
        data['tables'].append({'name': 'Specific Banner SR', 'rows': gen_table_rows(total_pulls, p_1_p_sr), 'color': '#D69E2E', 'bg': '#FFFFF0'})
    
    data['tables'].append({'name': 'Specific Off-Banner SR', 'rows': gen_table_rows(total_pulls, p_1_o_sr), 'color': '#718096', 'bg': '#F7FAFC'})
    data['tables'].append({'name': 'Specific Off-Banner SSR', 'rows': gen_table_rows(total_pulls, p_1_o_ssr), 'color': '#805AD5', 'bg': '#FAF5FF'})
    data['tables'].append({'name': 'Specific Banner SSR', 'rows': gen_table_rows(total_pulls, 0.0075), 'color': '#E53E3E', 'bg': '#FFF5F5'})

    return data

# ==========================================
#              HTML RENDERER
# ==========================================

def render_html(data):
    css = """
    <style>
        .gc-container { font-family: 'Segoe UI', Helvetica, sans-serif; color: #2D3748; }
        .gc-help { background: #EBF8FF; border-left: 4px solid #4299E1; padding: 10px 15px; margin-bottom: 20px; border-radius: 0 4px 4px 0; }
        .gc-help summary { cursor: pointer; font-weight: bold; color: #2B6CB0; outline: none; }
        .gc-help-content { margin-top: 10px; font-size: 0.9em; line-height: 1.5; color: #2C5282; }
        .gc-header { background: #1A202C; color: white; padding: 15px 20px; border-radius: 8px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
        .gc-pity-box { background: #2D3748; padding: 5px 15px; border-radius: 4px; font-size: 0.9em; border: 1px solid #4A5568; }
        .gc-grid-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }
        .gc-card { background: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .gc-big-num { font-size: 2em; font-weight: 800; margin-bottom: 10px; color: #2D3748; }
        .gc-stat-row { font-size: 0.85em; color: #4A5568; margin-bottom: 6px; display: flex; justify-content: space-between; }
        .gc-grid-tables { display: flex; flex-wrap: wrap; gap: 20px; justify-content: flex-start; }
        .gc-table-box { flex: 1 1 200px; max-width: 300px; background: white; border: 1px solid #E2E8F0; border-radius: 8px; overflow: hidden; }
        .gc-table-header { padding: 10px; font-weight: bold; border-bottom: 1px solid #E2E8F0; font-size: 0.95em; color: #1A202C; }
        .gc-table { width: 100%; border-collapse: collapse; font-size: 0.85em; }
        .gc-table th { text-align: left; padding: 8px; color: #718096; font-weight: 600; border-bottom: 2px solid #E2E8F0; background: #fff; }
        .gc-table td { padding: 6px 8px; border-bottom: 1px solid #EDF2F7; }
        .gc-table tr:last-child td { border-bottom: none; }
    </style>
    """

    html = f"""
    <div class="gc-container">
        {css}
        <details class="gc-help">
            <summary>❓ How to read these results (Click to expand)</summary>
            <div class="gc-help-content">
                <p><strong>1. Sigma (σ) Ranges</strong><br>
                A sigma is used to depict the standard deviation from the expected result. The ranges represent how likely you are to fall into this specific threshold. It is extremely unlikely you fall outside of the 3σ range.
                </p>
                <p><strong>2. Table Probabilities</strong><br>
                Probabilities in the tables are given both as probability of getting the <strong>exact count</strong>, and the probablity to get <strong>"exactly this or more"</strong>.
                </p>
                <p><strong>3. Table Legend</strong></p>
                <ul>
                    <li><strong>Total SSRs:</strong> The expected amount of all SSR cards you pull, both the banner and off-banner ones.</li>
                    <li><strong>Total SRs:</strong> The expected amount of all SR cards you pull.</li>
                    <li><strong>Specific Banner SSR:</strong> If there are two banner SSR cards but you're only interested in one, this is how many copies of that specific card you can expect to get.</li>
                    <li><strong>Specific Banner SR:</strong> If there is a banner SR, this is how many copies of that specific card you can expect.</li>
                    <li><strong>Specific Specific Off-Banner SR:</strong> How many copies of any off-banner SR card you can expect to get from your pulls.</li>
                    <li><strong>Specific Specific Off-Banner SSR:</strong> How many copies of any off-banner SR card you can expect to get from your pulls.</li>
                </ul>
            </div>
        </details>
        <div class="gc-header">
            <div style="font-size:1.1em"><strong>Results Analysis</strong></div>
            <div style="text-align:right">
                <div class="gc-pity-box" style="margin-bottom:4px">💰 Guaranteed Pity SSRs: <strong style="color:#68D391">{data['pity_count']}</strong></div>
                <div class="gc-pity-box">💳 Next Pity: <strong>{data['pity_next']}</strong> pulls</div>
            </div>
        </div>
    """

    html += '<div class="gc-grid-stats">'
    for stat in data['stats']:
        html += f"""
        <div class="gc-card" style="border-top: 4px solid {stat['color']}; background: {stat.get('bg', 'white')}">
            <h3 style="margin:0 0 10px 0; color: {stat['color']}">{stat['icon']} {stat['title']}</h3>
            <div class="gc-big-num">{stat['mu']:.2f}</div>
        """
        for i in range(1, 4):
            lower = max(0, math.floor(stat['mu'] - (i * stat['sigma'])))
            upper = math.ceil(stat['mu'] + (i * stat['sigma']))
            p = 0.5 * (1 + math.erf(((i*stat['sigma']) / (stat['sigma'] * math.sqrt(2))))) - \
                0.5 * (1 + math.erf(((-i*stat['sigma']) / (stat['sigma'] * math.sqrt(2)))))
            p_str = f"{p*100:.1f}%" if p <= 0.999 else ">99.9%"
            html += f"""<div class="gc-stat-row"><span><strong>{i}σ</strong> <span style="font-size:0.9em">({p_str})</span></span><span style="font-family:monospace; font-weight:bold; color:{stat['color']}">{lower} - {upper}</span></div>"""
        html += "</div>"
    html += '</div><div class="gc-grid-tables">'
    
    for tbl in data['tables']:
        c = tbl['color']
        bg = tbl['bg']
        html += f"""
        <div class="gc-table-box" style="border-top: 3px solid {c}">
            <div class="gc-table-header" style="background: {bg}; color: {c}">{tbl['name']}</div>
            <table class="gc-table"><tr><th style="width:20%">Cnt</th><th>Exact</th><th>This+</th></tr>
        """
        for row in tbl['rows']:
            cnt, p_exact, p_plus = row
            row_style = f'background: {bg}' if (p_plus > 0.5 and p_plus < 0.99) else ''
            html += f"<tr style='{row_style}'><td><span style='color:{c}; font-weight:bold'>{cnt}</span></td><td>{p_exact*100:.1f}%</td><td>{p_plus*100:.1f}%</td></tr>"
        html += "</table></div>"
    html += '</div></div>'
    return html

# ==========================================
#              STREAMLIT UI
# ==========================================

st.set_page_config(page_title="Shiraoki Pull Predictor", page_icon="🔮", layout="wide")

st.title("🔮 Shiraoki Pull Predictor")
st.markdown("---")

col_ui, col_res = st.columns([1, 2])

with col_ui:
    st.subheader("⚙️ Settings")
    w_pulls = st.number_input("Total Pulls", min_value=1, max_value=10000, value=200, step=1)
    w_mode = st.selectbox("Banner Type", ['2 Promo SSRs', '1 Promo SSR + 1 Promo SR'])
    
    c1, c2 = st.columns(2)
    w_pool_ssr = c1.number_input("Pool SSRs", value=45)
    w_pool_sr = c2.number_input("Pool SRs", value=33)
    
    if st.button("Tell me my odds, Shiraoki 🙇", type="primary", use_container_width=True):
        st.session_state.calculated = True

# Results Area
if 'calculated' in st.session_state:
    data = calculate_data(w_pulls, w_mode, w_pool_ssr, w_pool_sr)
    html_content = render_html(data)
    with col_res:
        st.components.v1.html(html_content, height=800, scrolling=True)
else:
    with col_res:
        st.info("👈 Set up and click Calculate!\n(Card count info accurate as of 18.12.2025)")
