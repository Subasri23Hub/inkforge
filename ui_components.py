"""INKFORGE v8 — All 7 spec fixes implemented."""
import streamlit as st
import streamlit.components.v1 as components
import json as _json
import re

# ─────────────────────────────────────────────────────────────────────────────
#  CSS  (via st.markdown — goes directly into Streamlit's page DOM)
# ─────────────────────────────────────────────────────────────────────────────
_MAIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,600&family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400;1,700&family=Crimson+Pro:ital,wght@0,400;0,500;0,600;1,400;1,600&family=Space+Mono:wght@400;700&display=swap');

:root {
  --ink:#111008; --ink3:#56523e; --ink4:#8a8470;
  --off:#f7f4ee; --rule:#e2dbd0; --ruled:#c5bdb0;
  --gold:#b8860b; --goldbg:#fdf8ee;
  --ft:'Playfair Display',Georgia,serif;
  --fb:'Crimson Pro',Georgia,serif;
  --fu:'Space Mono',monospace;
}

/* ── BASE ──────────────────────────────────────────────────────────── */
html,body,.stApp,.stApp>div,
[data-testid="stAppViewContainer"],[data-testid="stAppViewBlockContainer"],
[data-testid="block-container"],.block-container,
[data-testid="stMain"],section.main {
  background:#fff !important; color:#111008 !important;
}
.stApp { font-family:var(--fb) !important; }
.block-container { padding:16px 28px 60px !important; max-width:100% !important; }

/* ── MAIN CONTENT EXPANDS WHEN SIDEBAR HIDDEN ── */
[data-testid="stMain"] {
  width: 100% !important;
  flex: 1 1 auto !important;
  transition: all .25s ease !important;
}
.stApp > section:not([data-testid="stSidebar"]) {
  transition: margin-left .25s ease, width .25s ease !important;
}

/* Hide clutter only */
#MainMenu,footer,.stDeployButton,[data-testid="stToolbar"],
.stDecoration,[data-testid="stStatusWidget"] { display:none !important; }

/* ── SIDEBAR ───────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
  display:block !important; visibility:visible !important;
  background:#f7f4ee !important; min-width:220px !important;
  transform: none !important;
}
section[data-testid="stSidebar"] > div {
  display:block !important; visibility:visible !important;
}

/* Hide ONLY the native Streamlit collapse arrow — keep sidebar itself visible */
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"] {
  display: none !important;
  opacity: 0 !important;
  pointer-events: none !important;
}

/* ── SIDEBAR TOGGLE PILL — styles injected into parent doc via JS ── */



::-webkit-scrollbar{width:4px}
::-webkit-scrollbar-track{background:#f7f4ee}
::-webkit-scrollbar-thumb{background:#c5bdb0;border-radius:2px}

p,span,label,h1,h2,h3,h4,h5,li { color:#111008 !important; }
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] span { color:#111008 !important; }

/* ── FIX 1: CUSTOM CURSOR (pen nib, clean SVG) ────────────────────── */
*:not(input):not(textarea):not([contenteditable]) {
  cursor: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 20 20'%3E%3Cpath d='M3 17 L15 3' stroke='%23111008' stroke-width='1.4' stroke-linecap='round'/%3E%3Cpath d='M3 17 L6 11 L9 14 Z' fill='%23111008'/%3E%3Cpath d='M9 14 L15 3 L17 5 Z' fill='%23b8860b' opacity='0.9'/%3E%3C/svg%3E") 3 17, crosshair !important;
}
input, textarea, [contenteditable] { cursor: text !important; }

/* ═══════════════════════════════════════════════════════════════════
   BUTTONS — white default, black/white inversion ONLY on hover
   -webkit-text-fill-color beats all inline color styles from Streamlit
═══════════════════════════════════════════════════════════════════ */

/* ── Default state: always white bg, dark text ── */
.stButton > button,
.stDownloadButton > button {
  background: #ffffff !important;
  border: 1.5px solid #c5bdb0 !important;
  border-radius: 4px !important;
  font-family: 'Space Mono', monospace !important;
  font-size: 9px !important;
  font-weight: 700 !important;
  letter-spacing: .10em !important;
  text-transform: uppercase !important;
  box-shadow: none !important;
  padding: 8px 14px !important;
  white-space: nowrap !important;
  transition: background .18s ease, border-color .18s ease, color .18s ease !important;
}
.stButton > button *,
.stDownloadButton > button * {
  color: #111008 !important;
  -webkit-text-fill-color: #111008 !important;
  transition: color .18s ease, -webkit-text-fill-color .18s ease !important;
}

/* ── Hover ONLY: flip to black bg + white text ── */
.stButton > button:hover,
.stDownloadButton > button:hover {
  background: #111008 !important;
  border-color: #111008 !important;
}
.stButton > button:hover *,
.stDownloadButton > button:hover * {
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
}

/* ── TAB BUTTONS — scoped to .nf-tab-bar only ── */
.nf-tab-bar .stButton > button {
  background: #ffffff !important;
  border: 1.5px solid #c5bdb0 !important;
  border-radius: 4px !important;
  font-size: 10px !important;
  padding: 10px 8px !important;
  letter-spacing: .14em !important;
}
.nf-tab-bar .stButton > button * {
  color: #8a8470 !important;
  -webkit-text-fill-color: #8a8470 !important;
}
.nf-tab-bar .stButton > button:hover {
  background: #111008 !important;
  border-color: #111008 !important;
}
.nf-tab-bar .stButton > button:hover * {
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
}
/* Active tab state — nth-child set dynamically by inject_tab_css() in app.py */

/* ── Forge button — starts dark ── */
.nf-forge-btn .stButton > button {
  background: #111008 !important; border-color: #111008 !important;
  font-size: 11px !important; letter-spacing: .18em !important;
  height: 88px !important; min-height: 88px !important;
  width: 100% !important; min-width: 80px !important;
  padding: 0 12px !important;
  overflow: visible !important;
  white-space: nowrap !important;
}
.nf-forge-btn { width: 100%; min-width: 80px; }
.nf-forge-btn .stButton { width: 100%; }
.nf-forge-btn .stButton > button p { 
  color: #fff !important; 
  -webkit-text-fill-color: #fff !important;
  overflow: visible !important;
  white-space: nowrap !important;
  text-overflow: unset !important;
  font-size: 11px !important;
  letter-spacing: .18em !important;
}
.nf-forge-btn .stButton > button:hover { background: #b8860b !important; border-color: #b8860b !important; }

/* ── Add-to-book — gold ── */
.nf-atb .stButton > button {
  background: #fdf8ee !important; border-color: #b8860b !important;
  font-size: 8px !important; padding: 4px 12px !important;
}
.nf-atb .stButton > button * { color: #b8860b !important; -webkit-text-fill-color: #b8860b !important; }
.nf-atb .stButton > button:hover { background: #b8860b !important; border-color: #b8860b !important; }
.nf-atb .stButton > button:hover * { color: #fff !important; -webkit-text-fill-color: #fff !important; }

/* ── Workshop buttons — white default, black on hover ── */
/* .nf-wbtn div injected by st.markdown just before each workshop button */
.nf-wbtn + div .stButton > button,
.nf-wbtn ~ div .stButton > button {
  background: #fff !important; border: 1.5px solid #111008 !important;
  margin-top: 7px !important;
}
.nf-wbtn + div .stButton > button *,
.nf-wbtn ~ div .stButton > button * {
  color: #111008 !important; -webkit-text-fill-color: #111008 !important;
}
.nf-wbtn + div .stButton > button:hover,
.nf-wbtn ~ div .stButton > button:hover {
  background: #111008 !important; border-color: #111008 !important;
}
.nf-wbtn + div .stButton > button:hover *,
.nf-wbtn ~ div .stButton > button:hover * {
  color: #fff !important; -webkit-text-fill-color: #fff !important;
}

/* ── Chips — italic, rounded ── */
.nf-chips .stButton > button {
  border-radius: 20px !important;
  font-family: 'Crimson Pro', Georgia, serif !important;
  font-size: 11px !important; font-style: italic !important;
  text-transform: none !important; letter-spacing: 0 !important;
}

/* ── SEARCH BAR ─────────────────────────────────────────────────── */
section[data-testid="stSidebar"] .stTextInput input {
  background: #f5f2eb !important;
  border: 1px solid #d8d2c4 !important;
  border-radius: 6px !important;
  padding: 6px 12px !important;
  font-family: 'Space Mono', monospace !important;
  font-size: 9px !important;
  color: #111008 !important;
  height: 30px !important;
  box-shadow: none !important;
  letter-spacing: .03em !important;
}
section[data-testid="stSidebar"] .stTextInput input::placeholder {
  color: #555048 !important;
  font-style: italic !important;
}
section[data-testid="stSidebar"] .stTextInput input:focus {
  border-color: #b8860b !important;
  background: #fff !important;
  box-shadow: none !important;
}
section[data-testid="stSidebar"] .stTextInput label { display:none !important; }
section[data-testid="stSidebar"] .stTextInput { margin-bottom: 4px !important; }

/* ── STORY HISTORY LABEL ────────────────────────────────────────── */
.nf-hist-label {
  font-family:'Space Mono',monospace; font-size:8px; font-weight:700;
  letter-spacing:.28em; color:#8a8470; text-transform:uppercase;
  margin:10px 0 7px; border-bottom:1px solid #e2dbd0; padding-bottom:6px;
}

/* ── HISTORY CARD (HTML div) ─────────────────────────────────────── */
.nf-card-wrap {
  background: #fff;
  border: 1px solid #e2dbd0;
  border-left: 3px solid #c5bdb0;
  border-right: none;
  border-radius: 5px 0 0 5px;
  padding: 9px 10px 8px;
  cursor: pointer;
  transition: background .12s, border-left-color .12s;
  position: relative;
}
.nf-card-wrap:hover { background: #f5f2ed; border-left-color: #b8860b; }
.nf-card-title-txt {
  font-family: 'Cormorant Garamond', 'Playfair Display', Georgia, serif;
  font-size: 13.5px; font-weight: 600; color: #111008;
  line-height: 1.25; letter-spacing: .01em;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  margin-bottom: 3px;
}
.nf-card-meta-txt {
  font-family: 'Space Mono', monospace;
  font-size: 7px; color: #9a9488;
  letter-spacing: .03em; font-weight: 400; line-height: 1;
}
/* Hide the real Streamlit open button — card HTML handles click visually */
section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] [data-testid="stColumn"]:first-child .stButton {
  position: absolute !important; opacity: 0 !important;
  pointer-events: none !important;
  height: 0 !important; width: 0 !important; overflow: hidden !important;
  margin: 0 !important; padding: 0 !important;
}
section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] [data-testid="stColumn"]:first-child [data-testid="element-container"] {
  margin: 0 !important; padding: 0 !important;
}

/* ── THREE-DOT ⋯ BUTTON ─────────────────────────────────────────── */
section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] [data-testid="stColumn"]:last-child .stButton > button {
  background: #fff !important;
  border: 1px solid #e2dbd0 !important; border-left: none !important;
  border-radius: 0 5px 5px 0 !important;
  padding: 0 !important; width: 100% !important;
  height: 100% !important; min-height: 38px !important;
  letter-spacing: 0 !important; text-transform: none !important;
  box-shadow: none !important; margin-bottom: 0 !important;
  line-height: 1 !important;
}
section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] [data-testid="stColumn"]:last-child .stButton > button,
section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] [data-testid="stColumn"]:last-child .stButton > button * {
  color: #aaa8a0 !important; -webkit-text-fill-color: #aaa8a0 !important;
  font-size: 15px !important; letter-spacing: 0 !important; text-transform: none !important;
}
section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] [data-testid="stColumn"]:last-child .stButton > button:hover { background: #f0ede8 !important; }
section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] [data-testid="stColumn"]:last-child .stButton > button:hover,
section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] [data-testid="stColumn"]:last-child .stButton > button:hover * {
  color: #111008 !important; -webkit-text-fill-color: #111008 !important;
}

/* ── INLINE MENU DROPDOWN ────────────────────────────────────────── */
.nf-menu-box { margin: 2px 0 6px 0; }

section[data-testid="stSidebar"] .stButton > button[data-testid*="msh_"],
section[data-testid="stSidebar"] .stButton > button[data-testid*="mrn_"],
section[data-testid="stSidebar"] .stButton > button[data-testid*="mpi_"],
section[data-testid="stSidebar"] .stButton > button[data-testid*="mar_"],
section[data-testid="stSidebar"] .stButton > button[data-testid*="mde_"] {
  background: #fff !important;
  border: none !important; border-bottom: 1px solid #f0ece6 !important;
  border-left: 1px solid #e4dfd8 !important; border-right: 1px solid #e4dfd8 !important;
  border-radius: 0 !important;
  padding: 7px 14px !important;
  text-align: left !important; justify-content: flex-start !important;
  height: auto !important; min-height: 0 !important;
  width: 100% !important; box-shadow: none !important; margin: 0 !important;
  transition: background .1s !important;
}
/* First button — rounded top + top border + shadow */
section[data-testid="stSidebar"] .stButton > button[data-testid*="msh_"] {
  border-top: 1px solid #e4dfd8 !important;
  border-radius: 8px 8px 0 0 !important;
  box-shadow: 0 -2px 10px rgba(0,0,0,.05) !important;
}
/* Delete — rounded bottom + bottom shadow */
section[data-testid="stSidebar"] .stButton > button[data-testid*="mde_"] {
  border-bottom: 1px solid #e4dfd8 !important;
  border-radius: 0 0 8px 8px !important;
  box-shadow: 0 3px 10px rgba(0,0,0,.06) !important;
  margin-bottom: 4px !important;
}
/* Text styles */
section[data-testid="stSidebar"] .stButton > button[data-testid*="msh_"] p,
section[data-testid="stSidebar"] .stButton > button[data-testid*="mrn_"] p,
section[data-testid="stSidebar"] .stButton > button[data-testid*="mpi_"] p,
section[data-testid="stSidebar"] .stButton > button[data-testid*="mar_"] p {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
  font-size: 12px !important; font-weight: 400 !important;
  letter-spacing: 0 !important; text-transform: none !important;
  color: #1c1c1e !important; -webkit-text-fill-color: #1c1c1e !important;
  text-align: left !important;
}
section[data-testid="stSidebar"] .stButton > button[data-testid*="mde_"] p {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
  font-size: 12px !important; font-weight: 400 !important;
  letter-spacing: 0 !important; text-transform: none !important;
  color: #d0382b !important; -webkit-text-fill-color: #d0382b !important;
  text-align: left !important;
}
/* Hovers */
section[data-testid="stSidebar"] .stButton > button[data-testid*="msh_"]:hover,
section[data-testid="stSidebar"] .stButton > button[data-testid*="mrn_"]:hover,
section[data-testid="stSidebar"] .stButton > button[data-testid*="mpi_"]:hover,
section[data-testid="stSidebar"] .stButton > button[data-testid*="mar_"]:hover { background: #f5f2ed !important; }
section[data-testid="stSidebar"] .stButton > button[data-testid*="mde_"]:hover { background: #fdf2f2 !important; }


/* ── MENU BUTTON CONTAINER SPACING ─── */
section[data-testid="stSidebar"] [data-testid="element-container"]:has(> div > button[data-testid*="msh_"]),
section[data-testid="stSidebar"] [data-testid="element-container"]:has(> div > button[data-testid*="mrn_"]),
section[data-testid="stSidebar"] [data-testid="element-container"]:has(> div > button[data-testid*="mpi_"]),
section[data-testid="stSidebar"] [data-testid="element-container"]:has(> div > button[data-testid*="mar_"]),
section[data-testid="stSidebar"] [data-testid="element-container"]:has(> div > button[data-testid*="mde_"]) {
  margin-top: 0 !important; margin-bottom: 0 !important;
  padding: 0 !important;
}
/* ── RENAME SAVE/CANCEL BUTTONS ─────────────────────────────────── */
section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] .stButton > button {
  padding:5px 8px !important; font-size:8.5px !important;
  height:auto !important; min-height:0 !important;
  border-radius:4px !important; letter-spacing:.06em !important;
  text-transform:uppercase !important; font-family:'Space Mono',monospace !important;
  font-weight:700 !important; box-shadow:none !important; margin-bottom:6px !important;
}

/* ── FORMS ────────────────────────────────────────────────────────── */
.stSelectbox label,.stTextInput label,.stTextArea label,.stNumberInput label {
  font-family:var(--fu) !important; font-size:9px !important; font-weight:700 !important;
  letter-spacing:.2em !important; color:var(--ink3) !important; text-transform:uppercase !important;
}
.stSelectbox > div > div { background:#fff !important; border:1px solid var(--ruled) !important; border-radius:4px !important; color:#111008 !important; font-size:14px !important; }
.stSelectbox svg { fill:var(--ink4) !important; }
[data-testid="stSelectbox"] ul,[role="listbox"] { background:#fff !important; border:1px solid #111008 !important; border-radius:4px !important; }
[data-testid="stSelectbox"] li,[role="option"] { color:#111008 !important; background:#fff !important; }
[data-testid="stSelectbox"] li:hover,[role="option"]:hover { background:#f7f4ee !important; }
.stTextInput input { background:#fff !important; border:1px solid var(--ruled) !important; border-radius:4px !important; color:#111008 !important; font-size:14px !important; }
.stTextArea textarea { background:#fff !important; border:1px solid var(--ruled) !important; border-radius:4px !important; color:#111008 !important; font-size:15px !important; line-height:1.7 !important; }
.stTextArea textarea::placeholder { color:var(--ink4) !important; font-style:italic !important; }
.stNumberInput input { background:#fff !important; border:1px solid var(--ruled) !important; border-radius:4px !important; color:#111008 !important; font-family:var(--fu) !important; }
.stNumberInput button { background:#f7f4ee !important; border:1px solid var(--ruled) !important; color:#111008 !important; }
[data-testid="stRadio"] > label { font-family:var(--fu) !important; font-size:9px !important; font-weight:700 !important; letter-spacing:.18em !important; color:var(--ink3) !important; text-transform:uppercase !important; }
[data-testid="stRadio"] label p,[role="radiogroup"] label p { font-family:var(--fb) !important; font-size:14px !important; color:#111008 !important; }

/* ── PANEL TITLES ─────────────────────────────────────────────────── */
p.nf-panel-title,.nf-panel-title {
  font-family:var(--fu) !important; font-size:11px !important; font-weight:700 !important;
  letter-spacing:.28em !important; color:#111008 !important; text-transform:uppercase !important;
  padding-bottom:9px !important; border-bottom:1.5px solid var(--ruled) !important;
  margin-bottom:11px !important; margin-top:4px !important;
  display:block !important; background:none !important;
}

/* ── LAYOUT ELEMENTS ──────────────────────────────────────────────── */
.nf-stats-grid{display:grid;grid-template-columns:1fr 1fr;gap:5px;margin-top:7px}
.nf-stat{background:#fff;border:1px solid #e2dbd0;border-radius:4px;padding:9px;text-align:center}
.nf-stat-n{font-family:var(--ft);font-size:18px;font-weight:700;color:var(--gold);line-height:1;margin-bottom:3px}
.nf-stat-l{font-family:var(--fu);font-size:7px;letter-spacing:.18em;color:var(--ink3);text-transform:uppercase}
.nf-goal-track{height:4px;background:#e2dbd0;border-radius:2px;margin-bottom:5px;overflow:hidden}
.nf-goal-fill{height:100%;background:var(--gold);border-radius:2px}
.nf-goal-label{font-family:var(--fu);font-size:9px;color:var(--ink3);margin-bottom:7px}

.nf-nav{display:flex;align-items:center;justify-content:space-between;padding:10px 0 14px;border-bottom:2px solid #111008}
.nf-brand{display:flex;align-items:center;gap:12px}
.nf-brand-mark{width:36px;height:36px;border:2px solid #111008;border-radius:3px;display:flex;align-items:center;justify-content:center;font-family:var(--ft);font-size:17px;font-weight:900;color:#111008}
.nf-brand-name{font-family:var(--ft);font-size:20px;font-weight:900;letter-spacing:.22em;color:#111008;text-transform:uppercase;line-height:1}
.nf-brand-sub{font-family:var(--fu);font-size:8px;letter-spacing:.28em;color:#8a8470;text-transform:uppercase;margin-top:3px}
.nf-pills span{display:inline-block;padding:3px 10px;border:1px solid var(--ruled);border-radius:2px;font-family:var(--fu);font-size:9px;color:var(--ink3);background:#f7f4ee;margin:0 3px;text-transform:uppercase}
.nf-nav-right{display:flex;align-items:center;gap:20px}
.nf-progress{min-width:110px}
.nf-progress-bar{height:2px;background:#e2dbd0;border-radius:1px;overflow:hidden;margin-bottom:4px}
.nf-progress-fill{height:100%;background:var(--gold);border-radius:1px;transition:width .5s}
.nf-progress-lbl{font-family:var(--fu);font-size:8px;color:var(--ink3)}
.nf-wc-num{font-family:var(--ft);font-size:26px;font-weight:900;color:var(--gold);line-height:1}
.nf-wc-lbl{font-family:var(--fu);font-size:8px;letter-spacing:.22em;color:#8a8470;text-transform:uppercase}
.nf-tab-rule{height:1px;background:#e2dbd0;margin-bottom:20px;margin-top:4px}

.nf-ms-head{text-align:center;padding:24px 0 16px}
.nf-ms-rule{display:flex;align-items:center;justify-content:center;gap:10px;margin-bottom:12px}
.nf-ms-rule-line{height:1px;width:56px;background:#c5bdb0}
.nf-ms-rule-glyph{font-family:var(--ft);font-size:10px;color:#8a8470;letter-spacing:.35em}
.nf-ms-chapter{font-family:var(--fu);font-size:8px;letter-spacing:.4em;color:#8a8470;text-transform:uppercase;margin-bottom:9px}
.nf-ms-title{font-family:var(--ft);font-size:30px;font-weight:900;font-style:italic;color:#111008;line-height:1.15;margin-bottom:9px}
.nf-ms-meta{font-family:var(--fu);font-size:8px;letter-spacing:.2em;color:#8a8470;text-transform:uppercase}

.nf-user{padding:11px 16px;border-left:3px solid #c5bdb0;background:#f7f4ee;border-radius:0 4px 4px 4px;margin-bottom:5px}
.nf-user-label{font-family:var(--fu);font-size:7px;letter-spacing:.28em;color:#8a8470;text-transform:uppercase;margin-bottom:4px}
.nf-user-text{font-family:var(--fb);font-size:14px;font-style:italic;color:var(--ink3);line-height:1.6}
[data-testid="stExpander"]{border:1px solid #e2dbd0 !important;border-left:3px solid #111008 !important;border-radius:4px !important;margin-bottom:5px !important;background:#fff !important}
[data-testid="stExpander"] summary{font-family:var(--fu) !important;font-size:9px !important;font-weight:700 !important;letter-spacing:.1em !important;color:#111008 !important;text-transform:uppercase !important;padding:11px 14px !important}
[data-testid="stExpander"] summary:hover{background:#f7f4ee !important}
[data-testid="stExpander"] [data-testid="stExpanderContent"]{padding:0 14px 14px !important}
.nf-prose{background:#fff;border-top:2px solid #111008;padding:20px 30px}
.nf-prose-meta{display:flex;align-items:center;gap:7px;margin-bottom:13px}
.nf-badge{font-family:var(--fu);font-size:7px;font-weight:700;letter-spacing:.22em;color:#fff;background:#111008;padding:3px 9px;border-radius:2px;text-transform:uppercase}
.nf-badge-genre{font-family:var(--fu);font-size:7px;letter-spacing:.18em;color:var(--ink3);border:1px solid #c5bdb0;padding:3px 9px;border-radius:2px;text-transform:uppercase}
.nf-prose-ts{font-family:var(--fu);font-size:8px;color:#8a8470;margin-left:auto}
.nf-prose-body{font-family:var(--fb);font-size:17px;line-height:1.9;color:#111008;white-space:pre-wrap;word-break:break-word}
.nf-prose-body p{margin-bottom:.9em}
.nf-ch-break{display:flex;align-items:center;gap:14px;padding:16px 0}
.nf-ch-rule{flex:1;height:1px;background:linear-gradient(90deg,transparent,#c5bdb0)}
.nf-ch-rule.r{background:linear-gradient(90deg,#c5bdb0,transparent)}
.nf-ch-label{font-family:var(--ft);font-size:15px;font-style:italic;color:var(--ink3);letter-spacing:.16em}
.nf-streaming{font-family:var(--fb);font-size:17px;line-height:1.9;color:#111008;padding:24px 32px;background:#fff;border:1px solid #e2dbd0;border-top:3px solid var(--gold);white-space:pre-wrap}
.nf-empty{display:flex;flex-direction:column;align-items:center;text-align:center;padding:56px 36px}
.nf-empty-glyph{font-family:var(--ft);font-size:52px;color:#e2dbd0;margin-bottom:18px;animation:nfFloat 5s ease-in-out infinite}
@keyframes nfFloat{0%,100%{transform:translateY(0)}50%{transform:translateY(-7px)}}
.nf-empty-title{font-family:var(--ft);font-size:20px;font-style:italic;color:var(--ink3);margin-bottom:7px}
.nf-empty-sub{font-family:var(--fb);font-size:14px;color:#8a8470;max-width:360px;line-height:1.65}
/* FIX 6: Write zone — seamless, no top divider bar */
.nf-write-zone{background:#f7f4ee;border-radius:8px;padding:14px 14px 10px;margin-top:12px;border:none;}
.nf-write-zone .stTextArea textarea{background:#fff !important}
.nf-hidden-inputs{position:absolute;width:1px;height:1px;overflow:hidden;opacity:0;pointer-events:none;}
.nf-book-label{font-family:var(--fu);font-size:10px;font-weight:700;letter-spacing:.28em;color:var(--ink3);text-transform:uppercase;margin:18px 0 7px;border-bottom:1px solid #e2dbd0;padding-bottom:7px}
.nf-section-head{padding:4px 0 18px;border-bottom:2px solid #111008;margin-bottom:22px}
.nf-section-title{font-family:var(--ft);font-size:28px;font-weight:900;color:#111008;margin-bottom:4px}
.nf-section-sub{font-family:var(--fb);font-size:15px;font-style:italic;color:var(--ink3)}
.nf-wcard{background:#f7f4ee;border:1px solid #e2dbd0;border-top:3px solid #111008;border-radius:0 0 8px 8px;padding:20px 18px;margin-bottom:16px}
.nf-wcard-title{font-family:var(--ft);font-size:17px;font-weight:700;color:#111008;margin-bottom:3px}
.nf-wcard-sub{font-family:var(--fb);font-size:13px;font-style:italic;color:var(--ink3);margin-bottom:12px}
.nf-wcard .stTextArea textarea,.nf-wcard .stTextInput input{background:#fff !important;border:1px solid var(--ruled) !important;color:#111008 !important}
.nf-wout{background:#f7f4ee;border:1px solid #e2dbd0;border-left:4px solid #111008;border-radius:0 8px 8px 0;padding:22px 30px;margin-top:18px}
.nf-wout-label{font-family:var(--fu);font-size:8px;font-weight:700;letter-spacing:.28em;color:var(--ink3);text-transform:uppercase;margin-bottom:12px}
.nf-wout-text{font-family:var(--fb);font-size:15px;line-height:1.82;color:#111008;white-space:pre-wrap}
.nf-vault{background:#fff;border:1px solid #e2dbd0;border-top:3px solid #111008;border-radius:0 0 8px 8px;padding:26px 30px}
.nf-vault-title{font-family:var(--ft);font-size:26px;font-weight:900;font-style:italic;color:#111008;margin-bottom:5px}
.nf-vault-meta{font-family:var(--fu);font-size:8px;letter-spacing:.18em;color:#8a8470;text-transform:uppercase;margin-bottom:16px}
.nf-vault-empty{font-family:var(--fb);font-size:15px;font-style:italic;color:#8a8470;text-align:center;padding:44px 0}
.login-wrap{max-width:400px;margin:50px auto;padding:36px;background:#fff;border:1px solid #e2dbd0;border-top:4px solid #111008;border-radius:0 0 8px 8px;box-shadow:0 4px 28px rgba(0,0,0,.07)}
.login-logo{font-family:var(--ft);font-size:30px;font-weight:900;letter-spacing:.25em;color:#111008;text-transform:uppercase;text-align:center;margin-bottom:3px}
.login-sub{font-family:var(--fu);font-size:8px;letter-spacing:.28em;color:#8a8470;text-transform:uppercase;text-align:center;margin-bottom:28px}
.login-divider{display:flex;align-items:center;gap:10px;margin:18px 0}
.login-divider-line{flex:1;height:1px;background:#e2dbd0}
.login-divider-text{font-family:var(--fu);font-size:8px;color:#8a8470}
.nf-avatar{width:30px;height:30px;border-radius:50%;background:#111008;display:flex;align-items:center;justify-content:center;font-family:var(--ft);font-size:13px;font-weight:900;color:#fff}
.stSuccess{background:#f0faf4 !important;border:1px solid #2d8a5a !important;color:#1a5c38 !important}
.stError{background:#fef0f0 !important;border:1px solid #c0392b !important;color:#8b1a1a !important}
.stWarning{background:#fdf8ee !important;border:1px solid var(--gold) !important;color:var(--gold) !important}
</style>
"""

# ── FIX 1: Ink particle canvas via same-origin parent access ──────────────────
_INK_JS = """<!DOCTYPE html><html><head></head><body><script>
(function(){
  var par = (window.parent && window.parent !== window) ? window.parent : window;
  var pdoc = par.document;
  var oc = pdoc.getElementById('inkforge-drops');
  if(oc) oc.remove();
  var cv = pdoc.createElement('canvas');
  cv.id = 'inkforge-drops';
  cv.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:999998;';
  cv.width = par.innerWidth||1400; cv.height = par.innerHeight||900;
  pdoc.body.appendChild(cv);
  var ctx = cv.getContext('2d');
  var mx=0,my=0,lx=0,ly=0,drops=[];
  par.addEventListener('resize',function(){cv.width=par.innerWidth;cv.height=par.innerHeight;});
  pdoc.addEventListener('mousemove',function(e){
    mx=e.clientX; my=e.clientY;
    var spd=Math.sqrt((mx-lx)*(mx-lx)+(my-ly)*(my-ly));
    // Only emit drops outside input areas
    var t = pdoc.elementFromPoint(mx,my);
    var isInput = t && (t.tagName==='INPUT'||t.tagName==='TEXTAREA'||t.isContentEditable);
    if(!isInput && spd>8 && Math.random()<0.12){
      drops.push({x:mx+(Math.random()-.5)*3,y:my+(Math.random()-.5)*3,
        rx:Math.random()*1.8+0.5,ry:Math.random()*0.9+0.25,
        a:Math.random()*0.38+0.12,life:1,decay:Math.random()*0.028+0.012});
    }
    lx=mx;ly=my;
  });
  function frame(){
    ctx.clearRect(0,0,cv.width,cv.height);
    for(var i=drops.length-1;i>=0;i--){
      var d=drops[i];
      ctx.beginPath();
      ctx.ellipse(d.x,d.y,d.rx,d.ry,0,0,Math.PI*2);
      ctx.fillStyle='rgba(17,16,8,'+(d.a*d.life).toFixed(3)+')';
      ctx.fill();
      d.life-=d.decay;
      if(d.life<=0) drops.splice(i,1);
    }
    requestAnimationFrame(frame);
  }
  frame();
})();
</script></body></html>"""


_SIDEBAR_REOPEN_JS = """<!DOCTYPE html><html><head></head><body><script>
(function(){
  var par = (window.parent && window.parent !== window) ? window.parent : window;
  var pdoc = par.document;

  if (pdoc.getElementById('nf-sidebar-toggle')) return;

  // ── Inject pill + overlay CSS into parent document ─────────────
  var styleEl = pdoc.createElement('style');
  styleEl.id = 'nf-sidebar-toggle-style';
  styleEl.textContent = `
    #nf-sidebar-toggle {
      position: fixed !important;
      top: 50% !important;
      left: 0 !important;
      transform: translateY(-50%) !important;
      z-index: 2147483647 !important;
      background: #111008 !important;
      color: #fff !important;
      border: none !important;
      border-radius: 0 8px 8px 0 !important;
      width: 24px !important;
      height: 54px !important;
      cursor: pointer !important;
      font-size: 18px !important;
      font-weight: 900 !important;
      line-height: 1 !important;
      box-shadow: 3px 0 14px rgba(0,0,0,.3) !important;
      transition: background .15s ease, width .15s ease !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      padding: 0 !important;
      outline: none !important;
      margin: 0 !important;
    }
    #nf-sidebar-toggle:hover {
      background: #b8860b !important;
      width: 32px !important;
    }
    #nf-sidebar-toggle.nf-hidden {
      display: none !important;
    }
    /* When sidebar is open, shift pill right to sit flush against it */
    #nf-sidebar-toggle.nf-open {
      left: 244px !important;
      border-radius: 0 8px 8px 0 !important;
    }
  `;
  pdoc.head.appendChild(styleEl);

  // ── Create toggle pill ──────────────────────────────────────────
  var pill = pdoc.createElement('button');
  pill.id = 'nf-sidebar-toggle';
  pill.setAttribute('aria-label', 'Toggle sidebar');
  pdoc.body.appendChild(pill);

  var sidebarOpen = true; // assume open on load

  // ── Apply open state ────────────────────────────────────────────
  function openSidebar() {
    var sb = pdoc.querySelector('section[data-testid="stSidebar"]');
    if (!sb) return;
    sb.style.setProperty('display', 'block', 'important');
    sb.style.setProperty('visibility', 'visible', 'important');
    sb.style.setProperty('transform', 'translateX(0)', 'important');
    sb.style.setProperty('width', '244px', 'important');
    sb.style.setProperty('min-width', '244px', 'important');
    sb.style.setProperty('position', 'relative', 'important');
    sb.style.setProperty('flex-shrink', '0', 'important');
    var inner = sb.querySelector(':scope > div');
    if (inner) {
      inner.style.setProperty('transform', 'none', 'important');
      inner.style.setProperty('visibility', 'visible', 'important');
      inner.style.setProperty('display', 'block', 'important');
    }
    sidebarOpen = true;
    pill.innerHTML = '&#x00AB;'; // «
    pill.title = 'Close sidebar';
    pill.classList.add('nf-open');
    pill.classList.remove('nf-hidden');
  }

  // ── Apply closed state ──────────────────────────────────────────
  function closeSidebar() {
    var sb = pdoc.querySelector('section[data-testid="stSidebar"]');
    if (!sb) return;
    sb.style.setProperty('display', 'none', 'important');
    sidebarOpen = false;
    pill.innerHTML = '&#x00BB;'; // »
    pill.title = 'Open sidebar';
    pill.classList.remove('nf-open');
    pill.classList.remove('nf-hidden');
  }

  // ── Check if on login page ──────────────────────────────────────
  function isLoginPage() {
    // Login page has no sidebar user content
    var sb = pdoc.querySelector('section[data-testid="stSidebar"]');
    if (!sb) return true;
    var txt = sb.innerText || '';
    return txt.trim().length < 5;
  }

  // ── Toggle on click ─────────────────────────────────────────────
  pill.addEventListener('click', function(e) {
    e.stopPropagation();
    e.preventDefault();
    if (sidebarOpen) { closeSidebar(); }
    else { openSidebar(); }
  });

  // ── Init: show pill after a short delay so sidebar loads first ──
  setTimeout(function() {
    if (isLoginPage()) {
      pill.classList.add('nf-hidden');
    } else {
      openSidebar(); // ensure sidebar is visible on load
    }
  }, 300);

  // ── Keep checking login state (for after login/logout) ──────────
  setInterval(function() {
    if (isLoginPage()) {
      pill.classList.add('nf-hidden');
    } else {
      pill.classList.remove('nf-hidden');
    }
  }, 600);

})();
</script></body></html>"""

def inject_custom_css(logged_in: bool = False):
    st.markdown(_MAIN_CSS, unsafe_allow_html=True)
    components.html(_INK_JS, height=0, scrolling=False)
    if logged_in:
        components.html(_SIDEBAR_REOPEN_JS, height=0, scrolling=False)
    components.html("""<!DOCTYPE html><html><head></head><body><script>
(function(){
  var par = (window.parent && window.parent !== window) ? window.parent : window;
  var pdoc = par.document;

  /* Wire HTML card clicks → hidden Streamlit open button */
  function run() {
    var sb = pdoc.querySelector('section[data-testid="stSidebar"]');
    if (!sb) return;
    sb.querySelectorAll('.nf-card-wrap').forEach(function(card) {
      if (card._wired) return;
      card._wired = true;
      card.addEventListener('click', function() {
        var block = card.closest('[data-testid="stHorizontalBlock"]');
        if (!block) return;
        var col = block.querySelector('[data-testid="stColumn"]:first-child');
        if (!col) return;
        var btn = col.querySelector('button');
        if (btn) btn.click();
      });
    });
  }

  setInterval(run, 400);
  run();
})();
</script></body></html>""", height=0, scrolling=False)


def inject_tab_css(active_tab: str):
    """Fix 2: Inject dynamic CSS to mark the currently-active tab as black/white."""
    tab_order = {"forge": 1, "workshop": 2, "vault": 3, "compass": 4}
    n = tab_order.get(active_tab, 1)
    css = f"""<style>
/* Active tab #{n} — persistent black bg + white text */
/* .nf-tab-bar scopes this to ONLY the tab row, not workshop content columns */
.nf-tab-bar [data-testid="stColumn"]:nth-child({n}) .stButton > button {{
  background: #111008 !important;
  border-color: #111008 !important;
}}
.nf-tab-bar [data-testid="stColumn"]:nth-child({n}) .stButton > button * {{
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
}}
</style>"""
    st.markdown(css, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────

def _extract_characters(text: str) -> list:
    names = []
    patterns = [
        r'\b([A-Z][a-z]{2,})\s+said\b',    r'\bsaid\s+([A-Z][a-z]{2,})\b',
        r'\b([A-Z][a-z]{2,})\s+asked\b',   r'\b([A-Z][a-z]{2,})\s+whispered\b',
        r'\b([A-Z][a-z]{2,})\s+replied\b', r"\b([A-Z][a-z]{2,})'s\s+(?:eyes|voice|hand|face|heart)\b",
    ]
    stop = {"The","And","But","For","She","He","They","His","Her","Its","This","That",
            "With","From","Into","Upon","Then","When","Where","What","Which","There"}
    for pat in patterns:
        for m in re.findall(pat, text):
            if m not in stop and len(m) > 2 and m not in names:
                names.append(m)
    return names[:4]


def render_story_block(block: dict, block_index: int, on_chars_found=None, on_book_saved=None):
    btype = block.get("type", "story")
    if btype == "user":
        lmap = {"continue":"DIRECTION","enhance":"ENHANCE","rewrite":"REWRITE",
                "twist":"TWIST","dialogue":"DIALOGUE","describe":"DESCRIBE",
                "foreshadow":"FORESHADOW","stakes":"RAISE STAKES",
                "flashback":"FLASHBACK","chapter_end":"CHAPTER CLOSE"}
        st.markdown(f"""<div class="nf-user">
  <div class="nf-user-label">{lmap.get(block.get("action","continue"),"AUTHOR")} &nbsp;·&nbsp; {block.get('timestamp','')}</div>
  <div class="nf-user-text">{block['content']}</div>
</div>""", unsafe_allow_html=True)

    elif btype == "story":
        bmap = {"continue":"NARRATIVE","enhance":"ENHANCED","rewrite":"REWRITTEN",
                "twist":"PLOT TWIST","dialogue":"DIALOGUE","describe":"SCENE",
                "foreshadow":"FORESHADOW","stakes":"STAKES",
                "flashback":"FLASHBACK","chapter_end":"CHAPTER CLOSE"}
        badge   = bmap.get(block.get("action","continue"), "STORY")
        words   = block.get("words", len(block["content"].split()))
        in_book = block_index in st.session_state.get("book_passage_indices", [])
        preview = block["content"][:65].replace("\n"," ") + "…"
        body    = block["content"].replace("\n\n","</p><p>").replace("\n","<br>")
        tick    = "✓ " if in_book else ""
        story_idx = [i for i,b in enumerate(st.session_state.story_blocks) if b.get("type")=="story"]
        is_latest = bool(story_idx and block_index == story_idx[-1])
        with st.expander(f"{tick}{badge}  ·  {preview}", expanded=is_latest):
            st.markdown(f"""<div class="nf-prose">
  <div class="nf-prose-meta">
    <span class="nf-badge">{badge}</span>
    <span class="nf-badge-genre">{block.get('genre','')}</span>
    <span class="nf-prose-ts">{block.get('timestamp','')} · {words:,} words</span>
  </div>
  <div class="nf-prose-body"><p>{body}</p></div>
</div>""", unsafe_allow_html=True)
            edited_key = f"edited_{block_index}"
            if edited_key not in st.session_state:
                st.session_state[edited_key] = block["content"]
            if not in_book:
                with st.expander("✏  EDIT BEFORE ADDING TO BOOK", expanded=False):
                    new_text = st.text_area("Edit", value=st.session_state[edited_key],
                        height=180, key=f"edit_{block_index}", label_visibility="collapsed")
                    if new_text != st.session_state[edited_key]:
                        st.session_state[edited_key] = new_text

            st.markdown('<div class="nf-atb">', unsafe_allow_html=True)
            if not in_book:
                if st.button("+ ADD TO BOOK", key=f"atb_{block_index}"):
                    final = st.session_state.get(edited_key, block["content"])
                    st.session_state.story_blocks[block_index]["content"] = final
                    st.session_state.story_blocks[block_index]["words"] = len(final.split())
                    # Always build from scratch — never carry over indices from a previous story
                    current = list(st.session_state.get("book_passage_indices", []))
                    if block_index not in current:
                        current.append(block_index)
                    st.session_state["book_passage_indices"] = current

                    if on_book_saved:
                        on_book_saved()
                    st.rerun()
            else:
                st.button("✓ IN BOOK", key=f"atb_{block_index}", disabled=True)
            st.markdown('</div>', unsafe_allow_html=True)

    elif btype == "chapter_break":
        st.markdown(f"""<div class="nf-ch-break">
  <div class="nf-ch-rule"></div>
  <div class="nf-ch-label">{block['content']}</div>
  <div class="nf-ch-rule r"></div>
</div>""", unsafe_allow_html=True)


def render_empty_state():
    st.markdown("""<div class="nf-empty">
  <span class="nf-empty-glyph">I</span>
  <div class="nf-empty-title">Every great story begins with a single line.</div>
  <div class="nf-empty-sub">Type an opening, a premise, a feeling.<br>
  Your co-author will forge it into something extraordinary.</div>
</div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  FIX 5: TRUE OPEN BOOK — dual-page spread layout with auto pagination
# ─────────────────────────────────────────────────────────────────────────────
_LINES_PER_PAGE  = 16    # exactly 16 visual lines per page in the viewer
_CHARS_PER_LINE  = 45    # ~45 chars fit per justified line at 13px in the page width

def _para_lines(text: str) -> int:
    """Estimate how many visual lines a paragraph occupies."""
    import math
    chars = len(text.strip())
    if chars == 0:
        return 0
    # ceil(chars / chars_per_line) + 1 blank line gap after paragraph
    return math.ceil(chars / _CHARS_PER_LINE) + 1

def _paginate_text(paras_html: str) -> list:
    """Split paragraphs into pages of exactly _LINES_PER_PAGE visual lines."""
    paras = re.findall(r'<p>.*?</p>', paras_html, flags=re.DOTALL)
    if not paras:
        return [paras_html] if paras_html.strip() else []
    pages, cur, cur_lines = [], "", 0
    for p in paras:
        plain = re.sub(r'<[^>]+>', '', p)
        plines = _para_lines(plain)
        if cur_lines + plines > _LINES_PER_PAGE and cur:
            pages.append(cur)
            cur, cur_lines = p, plines
        else:
            cur += p
            cur_lines += plines
    if cur.strip():
        pages.append(cur)
    return pages


def render_book(story_blocks, book_indices, title, genre, chapter, word_count):
    """
    FIX 5: Dual-page open book.
    Spreads = pairs of [left_html, right_html].
    First spread: left = chapter title, right = first content page.
    Subsequent: left = even page, right = odd page.
    """
    # Build flat list of page HTML strings
    flat_pages: list[str] = []

    if book_indices:
        ch_map: dict = {}
        for idx in sorted(book_indices):
            if idx < len(story_blocks):
                b = story_blocks[idx]
                ch_map.setdefault(b.get("chapter_at_time", 1), []).append(b)

        for ch_num in sorted(ch_map.keys()):
            ch_title = title if ch_num == 1 else f"Chapter {ch_num}"
            # Chapter title — always its own page (will be left on first spread)
            flat_pages.append(
                f'<div class="bk-ch-head">'
                f'<div class="bk-ch-num">Chapter {ch_num}</div>'
                f'<div class="bk-ch-title">{ch_title}</div>'
                f'<div class="bk-ch-rule"></div>'
                f'</div>'
            )
            for passage in ch_map[ch_num]:
                raw = (passage["content"]
                       .replace("&","&amp;").replace("<","&lt;").replace(">","&gt;"))
                paras_html = "".join(
                    f"<p>{p.replace(chr(10),'<br>')}</p>"
                    for p in raw.split("\n\n") if p.strip()
                )
                for chunk in _paginate_text(paras_html):
                    flat_pages.append(f'<div class="bk-body">{chunk}</div>')

    # Build spreads: pairs [left, right]
    # If flat_pages is empty, spreads is empty too
    spreads: list[tuple] = []
    if flat_pages:
        i = 0
        while i < len(flat_pages):
            left = flat_pages[i]
            right = flat_pages[i+1] if i+1 < len(flat_pages) else ""
            spreads.append((left, right))
            i += 2

    total_spreads = len(spreads)
    spreads_js = _json.dumps([(l, r) for l, r in spreads])
    safe_title = title.replace('"','&quot;').replace("'","&#39;")
    dis_next = "disabled" if total_spreads <= 1 else ""

    empty_html = ("" if book_indices else
        '<div style="height:100%;display:flex;align-items:center;justify-content:center;'
        'font-family:\'Crimson Pro\',serif;font-size:13px;font-style:italic;color:#8a8470;'
        'text-align:center;padding:24px;">'
        'Press <b style="font-style:normal;color:#56523e;margin:0 4px">+ ADD TO BOOK</b>'
        '<br>on any passage to fill your book.</div>')

    spread_label = f"Spread 1 of {total_spreads}" if total_spreads else "Empty"

    components.html(f"""<!DOCTYPE html><html><head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,400&family=Crimson+Pro:ital,wght@0,400;1,400&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{
  background:#ccc7bc;
  display:flex; flex-direction:column; align-items:center;
  padding:10px 14px 12px;
  font-family:'Crimson Pro',serif;
  overflow:hidden; user-select:none;
}}

/* ── toolbar ── */
.bar{{
  display:flex; align-items:center; gap:5px; margin-bottom:10px;
  background:rgba(255,255,255,.92); padding:5px 14px;
  border-radius:14px; border:1px solid #c5bdb0;
  justify-content:center; flex-wrap:wrap; width:100%;
}}
.tl{{font-family:'Space Mono',monospace;font-size:7px;letter-spacing:.12em;color:#8a8470;text-transform:uppercase;}}
.tb{{
  background:#fff; border:1px solid #c5bdb0; border-radius:3px;
  padding:2px 8px; cursor:pointer; font-size:11px; color:#111008;
  min-width:24px; font-family:'Space Mono',monospace; font-weight:700;
  user-select:none; transition:all .12s;
}}
.tb:hover,.tb.on{{background:#111008;color:#fff;border-color:#111008;}}
.tb.gd{{background:#fdf8ee;border-color:#b8860b;color:#b8860b;}}
.tb.gd:hover,.tb.gd.on{{background:#b8860b;color:#fff;border-color:#b8860b;}}
.sep{{width:1px;height:13px;background:#c5bdb0;margin:0 3px;}}
.pgi{{font-family:'Space Mono',monospace;font-size:7px;color:#8a8470;margin-left:auto;white-space:nowrap;}}

/* ── OPEN BOOK SCENE ── */
.scene{{
  display:flex; justify-content:center; align-items:flex-start;
  width:100%;
}}

/* The whole open book (spine + left + gutter + right) */
.open-book{{
  display:flex; align-items:stretch;
  filter:drop-shadow(0 8px 24px rgba(0,0,0,.22));
  transform:perspective(1200px) rotateX(1deg);
  transition:transform .4s;
}}
.open-book:hover{{transform:perspective(1200px) rotateX(0deg);}}

/* Spine strip */
.spine{{
  width:16px; flex-shrink:0;
  background:linear-gradient(90deg,#0e0d09,#1a1912 40%,#0e0d09);
  border-radius:3px 0 0 3px;
}}

/* Left page */
.page-left{{
  width:285px; min-height:430px; max-height:430px;
  background:#f8f5ee;
  padding:24px 22px 28px 24px;
  overflow:hidden;
  border-right:1px solid #ddd7cc;
  position:relative;
  box-shadow:inset -8px 0 14px rgba(0,0,0,.07);
  background-image:repeating-linear-gradient(
    to bottom,transparent 0,transparent 19px,rgba(0,0,0,.006) 19px,rgba(0,0,0,.006) 20px);
}}
.page-left .pg-num{{
  position:absolute;bottom:10px;left:24px;
  font-family:'Space Mono',monospace;font-size:7px;color:#aaa8a0;
}}

/* Gutter (center fold) */
.gutter{{
  width:10px; flex-shrink:0;
  background:linear-gradient(90deg,
    rgba(0,0,0,.10) 0%,
    rgba(0,0,0,.04) 40%,
    rgba(0,0,0,.04) 60%,
    rgba(0,0,0,.10) 100%);
}}

/* Right page */
.page-right{{
  width:285px; min-height:430px; max-height:430px;
  background:#faf8f2;
  padding:24px 24px 28px 22px;
  overflow:hidden;
  position:relative;
  box-shadow:inset 8px 0 14px rgba(0,0,0,.05);
  border-radius:0 3px 3px 0;
  background-image:repeating-linear-gradient(
    to bottom,transparent 0,transparent 19px,rgba(0,0,0,.006) 19px,rgba(0,0,0,.006) 20px);
}}
.page-right .pg-num{{
  position:absolute;bottom:10px;right:24px;
  font-family:'Space Mono',monospace;font-size:7px;color:#aaa8a0;
}}

/* Page turn animation wrapper */
.page-inner{{
  height:100%;
  transform-origin:center center;
  transition:opacity .22s ease;
}}
.page-inner.fade-out{{opacity:0;}}
.page-inner.fade-in{{opacity:1;}}

/* Typography */
.bk-ch-head{{text-align:center;padding:32px 0 16px;}}
.bk-ch-num{{font-family:'Space Mono',monospace;font-size:7px;letter-spacing:.4em;color:#8a8470;text-transform:uppercase;margin-bottom:6px;}}
.bk-ch-title{{font-family:'Playfair Display',serif;font-size:18px;font-weight:900;color:#111008;line-height:1.25;}}
.bk-ch-rule{{width:42px;height:1px;background:#c5bdb0;margin:10px auto 0;}}
.bk-body{{
  font-family:'Crimson Pro',Georgia,serif;
  font-size:13px; line-height:1.55; color:#111008;
  text-align:justify; hyphens:auto;
}}
.bk-body p{{margin-bottom:.6em;text-indent:1.2em;}}
.bk-body p:first-child{{text-indent:0;}}

/* ── nav ── */
.nav{{display:flex;gap:10px;align-items:center;margin-top:10px;justify-content:center;}}
.nb{{
  background:#fff;border:1px solid #c5bdb0;border-radius:3px;
  padding:5px 16px;cursor:pointer;
  font-family:'Space Mono',monospace;font-size:7px;font-weight:700;
  letter-spacing:.1em;color:#111008;transition:all .12s;
  text-transform:uppercase;user-select:none;
}}
.nb:hover{{background:#111008;color:#fff;border-color:#111008;}}
.nb:disabled{{opacity:.25;cursor:default;pointer-events:none;}}
.pct{{font-family:'Space Mono',monospace;font-size:7px;color:#8a8470;min-width:80px;text-align:center;}}
</style>
</head><body>

<div class="bar">
  <span class="tl">Sel:&nbsp;</span>
  <button class="tb" onclick="fmt('bold')"><b>B</b></button>
  <button class="tb" onclick="fmt('italic')"><i>I</i></button>
  <button class="tb" onclick="fmt('underline')"><u>U</u></button>
  <div class="sep"></div>
  <button class="tb gd on" id="bs" onclick="setF('serif')">Serif</button>
  <button class="tb"       id="bn" onclick="setF('sans')">Sans</button>
  <div class="sep"></div>
  <span class="pgi" id="pgi">{spread_label}</span>
</div>

<div class="scene">
  <div class="open-book">
    <div class="spine"></div>

    <!-- LEFT PAGE -->
    <div class="page-left">
      <div class="page-inner" id="left-inner" contenteditable="true">{empty_html if not book_indices else ""}</div>
      <span class="pg-num" id="left-pgn"></span>
    </div>

    <!-- GUTTER -->
    <div class="gutter"></div>

    <!-- RIGHT PAGE -->
    <div class="page-right">
      <div class="page-inner" id="right-inner" contenteditable="true"></div>
      <span class="pg-num" id="right-pgn"></span>
    </div>
  </div>
</div>

<div class="nav">
  <button class="nb" id="bp"  onclick="go(-1)" disabled>← Previous</button>
  <span   class="pct" id="pct">{"1 / "+str(total_spreads) if total_spreads else "—"}</span>
  <button class="nb" id="bnx" onclick="go(1)" {dis_next}>Next →</button>
</div>

<script>
var spreads = {spreads_js};
var cur = 0;

function fmt(c) {{ document.execCommand(c, false, null); }}

function setF(f) {{
  var ff = f==='sans'?'Arial,Helvetica,sans-serif':"'Crimson Pro',Georgia,serif";
  document.getElementById('bs').className='tb gd'+(f==='serif'?' on':'');
  document.getElementById('bn').className='tb'+(f==='sans'?' gd on':'');
  document.querySelectorAll('.bk-body,.bk-body p').forEach(function(n){{n.style.fontFamily=ff;}});
}}

function ui() {{
  var n = spreads.length;
  var li = document.getElementById('left-inner');
  var ri = document.getElementById('right-inner');
  var lpg = document.getElementById('left-pgn');
  var rpg = document.getElementById('right-pgn');

  if (!n) {{
    document.getElementById('pct').textContent = '—';
    document.getElementById('pgi').textContent = 'Empty';
    document.getElementById('bp').disabled = true;
    document.getElementById('bnx').disabled = true;
    return;
  }}

  var spread = spreads[cur];
  li.innerHTML = spread[0];
  ri.innerHTML = spread[1] || '';

  // Page numbers: left = 2*cur+1, right = 2*cur+2
  var lnum = cur * 2 + 1;
  var rnum = cur * 2 + 2;
  lpg.textContent = lnum;
  rpg.textContent = spread[1] ? rnum : '';

  document.getElementById('pct').textContent = (cur+1)+' / '+n;
  document.getElementById('pgi').textContent = 'Spread '+(cur+1)+' of '+n;
  document.getElementById('bp').disabled  = (cur === 0);
  document.getElementById('bnx').disabled = (cur >= n-1);
}}

function go(dir) {{
  if (!spreads.length) return;
  var nxt = cur + dir;
  if (nxt < 0 || nxt >= spreads.length) return;

  // Fade out
  var li = document.getElementById('left-inner');
  var ri = document.getElementById('right-inner');
  li.classList.add('fade-out');
  ri.classList.add('fade-out');

  setTimeout(function() {{
    cur = nxt;
    li.innerHTML = spreads[cur][0];
    ri.innerHTML = spreads[cur][1] || '';

    var lnum = cur * 2 + 1;
    var rnum = cur * 2 + 2;
    document.getElementById('left-pgn').textContent  = lnum;
    document.getElementById('right-pgn').textContent = spreads[cur][1] ? rnum : '';
    document.getElementById('pct').textContent = (cur+1)+' / '+spreads.length;
    document.getElementById('pgi').textContent = 'Spread '+(cur+1)+' of '+spreads.length;
    document.getElementById('bp').disabled  = (cur === 0);
    document.getElementById('bnx').disabled = (cur >= spreads.length-1);

    li.classList.remove('fade-out');
    ri.classList.remove('fade-out');
  }}, 180);
}}

ui();
</script>
</body></html>""", height=560, scrolling=False)


def generate_book_pdf(story_blocks, book_indices, title, genre="", tone="", author="INKFORGE"):
    """Print-ready PDF: cream pages, dark spine cover, drop caps, chapter headers,
    alternating page numbers, bold/italic/underline preserved. A5 format."""
    import io, re, subprocess, sys, os, platform
    try:
        from reportlab.lib.pagesizes import A5
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab", "--quiet"])
    from reportlab.lib.pagesizes import A5
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate,
                                    Paragraph, Spacer, PageBreak, NextPageTemplate,
                                    KeepTogether)
    from reportlab.platypus.flowables import HRFlowable
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER

    # ── Font paths: Windows / Linux / Mac ───────────────────────────
    _sys = platform.system()
    if _sys == "Windows":
        # Use Georgia (serif) + Arial (sans) — always present on Windows
        _wf = os.path.join(os.environ.get("WINDIR","C:\\Windows"), "Fonts")
        _font_map = [
            ('BookSerif',        os.path.join(_wf,'georgia.ttf')),
            ('BookSerif-Bold',   os.path.join(_wf,'georgiab.ttf')),
            ('BookSerif-Italic', os.path.join(_wf,'georgiai.ttf')),
            ('BookSerif-BI',     os.path.join(_wf,'georgiaz.ttf')),
            ('BookSans',         os.path.join(_wf,'arial.ttf')),
            ('BookSans-Bold',    os.path.join(_wf,'arialbd.ttf')),
            ('BookSans-Italic',  os.path.join(_wf,'ariali.ttf')),
            ('BookSans-BI',      os.path.join(_wf,'arialbi.ttf')),
        ]
    elif _sys == "Darwin":
        _mf = "/Library/Fonts"
        _font_map = [
            ('BookSerif',        os.path.join(_mf,'Georgia.ttf')),
            ('BookSerif-Bold',   os.path.join(_mf,'Georgia Bold.ttf')),
            ('BookSerif-Italic', os.path.join(_mf,'Georgia Italic.ttf')),
            ('BookSerif-BI',     os.path.join(_mf,'Georgia Bold Italic.ttf')),
            ('BookSans',         '/System/Library/Fonts/Helvetica.ttc'),
            ('BookSans-Bold',    '/System/Library/Fonts/Helvetica.ttc'),
            ('BookSans-Italic',  '/System/Library/Fonts/Helvetica.ttc'),
            ('BookSans-BI',      '/System/Library/Fonts/Helvetica.ttc'),
        ]
    else:
        _lf = '/usr/share/fonts/truetype/crosextra/'
        _font_map = [
            ('BookSerif',        _lf+'Caladea-Regular.ttf'),
            ('BookSerif-Bold',   _lf+'Caladea-Bold.ttf'),
            ('BookSerif-Italic', _lf+'Caladea-Italic.ttf'),
            ('BookSerif-BI',     _lf+'Caladea-BoldItalic.ttf'),
            ('BookSans',         _lf.replace('crosextra','crosextra')+'Carlito-Regular.ttf'),
            ('BookSans-Bold',    _lf+'Carlito-Bold.ttf'),
            ('BookSans-Italic',  _lf+'Carlito-Italic.ttf'),
            ('BookSans-BI',      _lf+'Carlito-BoldItalic.ttf'),
        ]

    _registered = set(pdfmetrics.getRegisteredFontNames())
    for name, path in _font_map:
        if name not in _registered:
            try: pdfmetrics.registerFont(TTFont(name, path))
            except: pass
    try:
        pdfmetrics.registerFontFamily('BookSerif', normal='BookSerif', bold='BookSerif-Bold',
                                      italic='BookSerif-Italic', boldItalic='BookSerif-BI')
        pdfmetrics.registerFontFamily('BookSans',  normal='BookSans',  bold='BookSans-Bold',
                                      italic='BookSans-Italic',  boldItalic='BookSans-BI')
    except: pass

    C_PAGE=HexColor('#f8f5ee'); C_INK=HexColor('#111008'); C_GOLD=HexColor('#b8860b')
    C_RULE=HexColor('#c5bdb0'); C_META=HexColor('#8a8470'); C_SPINE=HexColor('#1a1912')
    W, H = A5
    ML, MR, MT, MB = 22*mm, 16*mm, 20*mm, 22*mm

    page_nums = [0]

    def draw_page(canvas, doc):
        canvas.saveState()
        # Full page cream background
        canvas.setFillColor(C_PAGE); canvas.rect(0,0,W,H,fill=1,stroke=0)

        pn = page_nums[0]
        inner = MR if pn%2==0 else ML
        outer = ML if pn%2==0 else MR

        # ── Header ──
        canvas.setStrokeColor(C_RULE); canvas.setLineWidth(0.35)
        canvas.line(inner, H-MT+5*mm, W-outer, H-MT+5*mm)
        canvas.setFont('BookSans', 7); canvas.setFillColor(C_META)
        canvas.drawCentredString(W/2, H-MT+7*mm, title.upper())

        # ── Footer ──
        canvas.line(inner, MB-4*mm, W-outer, MB-4*mm)
        canvas.setFont('BookSans', 8); canvas.setFillColor(C_META)
        if pn%2==0: canvas.drawString(inner, MB-7*mm, str(pn))
        else: canvas.drawRightString(W-outer, MB-7*mm, str(pn))
        page_nums[0] += 1

        # ── HARD MASK — paint over anything outside header/footer rules only ──
        canvas.setFillColor(C_PAGE)
        canvas.rect(0, 0, W, MB-4*mm, fill=1, stroke=0)       # below footer rule
        canvas.rect(0, H-MT+5*mm, W, MT, fill=1, stroke=0)    # above header rule

        canvas.restoreState()

    def draw_chapter(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(C_PAGE); canvas.rect(0,0,W,H,fill=1,stroke=0)
        # Bottom mask on chapter pages
        canvas.rect(0, 0, W, MB-4*mm, fill=1, stroke=0)
        canvas.restoreState()

    def draw_cover(canvas, doc):
        """Clean cream cover — title centred in upper third, gold rule, genre, footer."""
        canvas.saveState()
        # Full cream background — no black spine
        canvas.setFillColor(C_PAGE); canvas.rect(0,0,W,H,fill=1,stroke=0)
        # Thin border
        canvas.setStrokeColor(C_RULE); canvas.setLineWidth(0.5)
        canvas.rect(8*mm, 8*mm, W-16*mm, H-16*mm, fill=0, stroke=1)
        # Title — upper third
        canvas.setFont('BookSerif-Bold', 28); canvas.setFillColor(C_INK)
        # Simple single-line title centred
        canvas.drawCentredString(W/2, H*0.62, title)
        # Gold rule under title
        canvas.setStrokeColor(C_GOLD); canvas.setLineWidth(1.0)
        canvas.line(W/2-22*mm, H*0.62-8*mm, W/2+22*mm, H*0.62-8*mm)
        # Genre label
        if genre:
            canvas.setFont('BookSans', 8); canvas.setFillColor(C_GOLD)
            canvas.drawCentredString(W/2, H*0.62-16*mm, genre.upper())
        # Footer
        canvas.setFont('BookSans-Italic', 8); canvas.setFillColor(C_META)
        canvas.drawCentredString(W/2, 16*mm, f'Written with {author}')
        canvas.restoreState()

    s_body   = ParagraphStyle('body', fontName='BookSerif', fontSize=11.5, leading=19,
                  textColor=C_INK, firstLineIndent=16, spaceAfter=0,
                  spaceBefore=8, alignment=TA_JUSTIFY)
    s_first  = ParagraphStyle('first', parent=s_body, firstLineIndent=0,
                  spaceAfter=0, spaceBefore=0)
    s_chnum  = ParagraphStyle('chnum', fontName='BookSans', fontSize=7.5, leading=11,
                  textColor=C_META, alignment=TA_CENTER, spaceAfter=4)
    s_chtitle= ParagraphStyle('chtitle', fontName='BookSerif-Bold', fontSize=24, leading=30,
                  textColor=C_INK, alignment=TA_CENTER, spaceAfter=6)
    s_orn    = ParagraphStyle('orn', fontName='BookSerif', fontSize=11, leading=14,
                  textColor=C_RULE, alignment=TA_CENTER, spaceAfter=12, spaceBefore=12)
    s_dropcap_cap  = ParagraphStyle('dcc', fontName='BookSerif-Bold', fontSize=38, leading=38,
                  textColor=C_INK, alignment=TA_JUSTIFY)
    s_dropcap_rest = ParagraphStyle('dcr', fontName='BookSerif', fontSize=11.5, leading=19,
                  textColor=C_INK, firstLineIndent=0, spaceAfter=6, alignment=TA_JUSTIFY)

    def _markup(text):
        t = text.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
        t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
        t = re.sub(r'\*(.+?)\*',     r'<i>\1</i>', t)
        t = re.sub(r'__(.+?)__',     r'<u>\1</u>', t)
        return t

    def _drop_cap(text):
        """Elegant drop cap — large first letter top-aligned, body text wraps from top-right."""
        from reportlab.platypus import Table, TableStyle
        text = text.strip()
        if not text: return None
        cap  = text[0].upper()
        rest = _markup(text[1:])
        cap_w  = 11*mm
        body_w = W - ML - MR - cap_w - 4*mm
        cap_para  = Paragraph(cap, s_dropcap_cap)
        rest_para = Paragraph(rest, s_dropcap_rest)
        tbl = Table([[cap_para, rest_para]], colWidths=[cap_w, body_w])
        tbl.setStyle(TableStyle([
            ('VALIGN',         (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING',    (0,0), (0,0), 0),
            ('RIGHTPADDING',   (0,0), (0,0), 5),
            ('LEFTPADDING',    (1,0), (1,0), 0),
            ('TOPPADDING',     (0,0), (0,0), -6),   # pull cap UP so top aligns with text
            ('TOPPADDING',     (1,0), (1,0), 0),
            ('BOTTOMPADDING',  (0,0), (-1,-1), 0),
        ]))
        return tbl

    # Cover = page 1. NextPageTemplate('body') fires on the PageBreak so page 2 = body.
    flowables = [NextPageTemplate('cover')]
    flowables.append(Spacer(1, 1))
    flowables.append(NextPageTemplate('body'))
    flowables.append(PageBreak())

    if book_indices:
        ch_map = {}
        for idx in sorted(book_indices):
            if idx < len(story_blocks):
                b = story_blocks[idx]
                ch_map.setdefault(b.get('chapter_at_time', 1), []).append(b)

        for ch_num in sorted(ch_map.keys()):
            ch_title_text = title if ch_num == 1 else f'Chapter {ch_num}'
            flowables.append(PageBreak())
            flowables.append(Spacer(1, 28*mm))
            flowables.append(Paragraph(f'CHAPTER {ch_num}', s_chnum))
            flowables.append(Spacer(1, 3*mm))
            flowables.append(Paragraph(ch_title_text, s_chtitle))
            flowables.append(HRFlowable(width='20%', thickness=0.5, color=C_RULE,
                                        hAlign='CENTER', spaceAfter=12*mm))
            # Story content — plain paragraphs, free-flowing across pages, no drop cap
            first_para = True
            for passage in ch_map[ch_num]:
                for p in [x.strip() for x in passage.get('content','').split('\n\n') if x.strip()]:
                    if first_para:
                        flowables.append(Paragraph(_markup(p), s_first))
                        first_para = False
                    else:
                        flowables.append(Paragraph(_markup(p), s_body))
            flowables.append(Paragraph('\u2726  \u2726  \u2726', s_orn))

    buf = io.BytesIO()
    # Frame height: snap to exact multiple of leading so lines never get clipped.
    # PDF frame: fill naturally — as many lines as fit the page with proper spacing.
    # Anchored to top margin, bottom stops just above the footer rule.
    _leading   = 19
    _frame_top = H - MT                      # just inside top margin
    _frame_bot = MB                          # sits on bottom margin, above footer
    _usable    = _frame_top - _frame_bot
    _lines_fit = int(_usable / _leading)     # how many whole lines fit
    _snapped_h = _lines_fit * _leading       # snap to whole lines — no half-line cuts
    _frame_y   = _frame_top - _snapped_h    # top-anchored

    frame_cover = Frame(0, 0, W, H, id='cf', showBoundary=0)
    frame_body  = Frame(
        ML,
        _frame_y,
        W - ML - MR,
        _snapped_h,
        id='bf', showBoundary=0)

    doc = BaseDocTemplate(buf, pagesize=A5,
        leftMargin=ML, rightMargin=MR, topMargin=MT, bottomMargin=MB,
        title=title, author=author,
        creator='INKFORGE Story Intelligence Engine',
        subject=f'{genre} · {tone}')
    doc.addPageTemplates([
        PageTemplate(id='cover',   frames=[frame_cover], onPage=draw_cover),
        PageTemplate(id='chapter', frames=[frame_body],  onPage=draw_chapter),
        PageTemplate(id='body',    frames=[frame_body],  onPage=draw_page),
    ])
    doc.build(flowables)
    return buf.getvalue()

def render_book_export(story_blocks, book_indices, title):
    if not book_indices: return ""
    lines = [title.upper(), "="*len(title), ""]
    cur_ch = None
    for idx in sorted(book_indices):
        if idx < len(story_blocks):
            b = story_blocks[idx]
            ch = b.get("chapter_at_time", 1)
            if ch != cur_ch:
                cur_ch = ch
                lines.append(f"\n\nCHAPTER {ch}\n{'─'*40}\n")
            lines.append(b["content"] + "\n")
    return "\n".join(lines)
