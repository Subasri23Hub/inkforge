import streamlit as st
import requests
import json
import secrets
import re
from datetime import datetime
from story_engine import StoryEngine, GUARD_SYSTEM, get_poetic_refusal
from ui_components import (inject_custom_css, inject_tab_css, render_story_block,
                            render_empty_state, render_book, render_book_export,
                            generate_book_pdf)
from auth import (register_user, login_user, logout,
                  get_current_user, load_history,
                  save_session_to_history, delete_history_entry,
                  rename_history_entry, pin_history_entry,
                  archive_history_entry, generate_share_token)

st.set_page_config(page_title="INKFORGE", page_icon="I", layout="wide",
                   initial_sidebar_state="expanded")
# ── Daily word count reset ──────────────────────────────────────
from datetime import date as _date
_today = str(_date.today())
if st.session_state.get("daily_date") != _today:
    st.session_state["daily_date"]  = _today
    st.session_state["daily_words"] = 0

inject_custom_css(logged_in=bool(st.session_state.get("auth_token","")))
engine = StoryEngine()
OLLAMA_URL = "http://localhost:11434"

def story_defaults():
    return {"story_blocks":[],"genre":"Fantasy","tone":"Cinematic","pov":"Third Person",
            "ollama_model":"llama3","word_count":0,"chapter":1,
            "story_title":"Untitled Manuscript","characters":[],"story_context":"",
            "active_tab":"forge","writing_goal":1000,"session_words":0,"daily_date":"","daily_words":0,
            "workshop_result":"","workshop_type":"","mood":"Neutral",
            "book_passage_indices":[],"session_id":secrets.token_hex(8),
}

if "auth_token" not in st.session_state:
    st.session_state.auth_token = ""
for k,v in story_defaults().items():
    if k not in st.session_state:
        st.session_state[k] = v

def get_models():
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        if r.status_code == 200:
            return [m["name"] for m in r.json().get("models",[])]
    except: pass
    return []



def auto_save():
    user = get_current_user()
    if user and st.session_state.story_blocks:
        save_session_to_history(user["username"],{
            "session_id":st.session_state.session_id,
            "story_title":st.session_state.story_title,
            "word_count":st.session_state.word_count,
            "genre":st.session_state.genre,"tone":st.session_state.tone,
            "chapter":st.session_state.chapter,
            "story_blocks":st.session_state.story_blocks,
            "book_passage_indices":st.session_state.book_passage_indices,
            "characters":st.session_state.characters,
            "story_context":st.session_state.story_context,
            "pov":st.session_state.pov})

def process_story(instruction, action_type="continue"):
    existing = "\n\n".join(b["content"] for b in st.session_state.story_blocks if b["type"]=="story")
    # ── GUARDRAIL: block non-story requests with poetic refusal ──
    guard = engine.is_story_related(
        user_text=instruction,
        existing_story=existing,
        story_context=st.session_state.story_context,
        characters=st.session_state.characters,
        action_type=action_type,
    )
    if not guard.allowed:
        st.markdown(f'<div class="nf-wout"><div class="nf-wout-label">INKFORGE SPEAKS</div><div class="nf-wout-text">{get_poetic_refusal()}</div></div>', unsafe_allow_html=True)
        return
    sys_p = engine.build_system_prompt(
        genre=st.session_state.genre,tone=st.session_state.tone,
        pov=st.session_state.pov,action_type=action_type,
        existing_story=existing,characters=st.session_state.characters,
        story_title=st.session_state.story_title,
        mood=st.session_state.mood,
        world_context=st.session_state.story_context)
    usr_m = engine.build_user_message(instruction=instruction,action_type=action_type,existing_story=existing)
    if instruction.strip() and not instruction.startswith("__"):
        st.session_state.story_blocks.append({"type":"user","content":instruction,
            "action":action_type,"timestamp":datetime.now().strftime("%H:%M"),
            "chapter_at_time":st.session_state.chapter})
    payload={"model":st.session_state.ollama_model,
        "messages":[{"role":"system","content":sys_p},{"role":"user","content":usr_m}],
        "stream":True,"options":{"temperature":0.78,"top_p":0.88,"repeat_penalty":1.04,"num_predict":500,"num_ctx":1024,"stop":["\n\n\n","---"]}}
    with st.spinner(""):
        try:
            resp = requests.post(f"{OLLAMA_URL}/api/chat",json=payload,stream=True,timeout=180)
            resp.raise_for_status()
            full=""
            ph=st.empty()
            chunk_ctr=0
            for line in resp.iter_lines():
                if not line: continue
                try:
                    c=json.loads(line.decode())
                    tok=c.get("message",{}).get("content","")
                    if tok:
                        full+=tok
                        chunk_ctr+=1
                        if chunk_ctr%25==0:
                            ph.markdown(f'<div class="nf-streaming">{full}▌</div>',unsafe_allow_html=True)
                    if c.get("done"): break
                except: continue
            ph.empty()
            if full:
                wc=len(full.split())
                st.session_state.word_count+=wc
                st.session_state.session_words+=wc
                st.session_state["daily_words"] = st.session_state.get("daily_words", 0) + wc

                if st.session_state.story_title=="Untitled Manuscript":
                    t = engine.extract_title_suggestion(full,
                            model=st.session_state.ollama_model,
                            ollama_url=OLLAMA_URL)
                    if t:
                        st.session_state.story_title = t
                        pass  # st.rerun() below will re-render title input with new value
                st.session_state.story_blocks.append({"type":"story","content":full,
                    "action":action_type,"timestamp":datetime.now().strftime("%H:%M"),
                    "words":wc,"genre":st.session_state.genre,"tone":st.session_state.tone,
                    "chapter_at_time":st.session_state.chapter})
                auto_save()
                st.rerun()
        except requests.exceptions.ConnectionError: st.error("Ollama not running — start: ollama serve")
        except Exception as e: st.error(f"Error: {e}")

def workshop_query(prompt,result_type):
    # ── GUARDRAIL: only allow story/craft related workshop queries ──
    guard = engine.is_story_related(
        user_text=prompt,
        existing_story="\n\n".join(b["content"] for b in st.session_state.story_blocks if b["type"]=="story"),
        story_context=st.session_state.story_context,
        characters=st.session_state.characters,
        action_type="continue",
    )
    if not guard.allowed:
        st.session_state.workshop_result = get_poetic_refusal()
        st.session_state.workshop_type = "INKFORGE SPEAKS"
        st.rerun()
        return
    payload={"model":st.session_state.ollama_model,
        "messages":[{"role":"system","content":GUARD_SYSTEM+"\nYou are an expert creative writing coach."},
                    {"role":"user","content":prompt}],
        "stream":True,"options":{"temperature":0.7,"num_predict":500,"num_ctx":1024}}
    with st.spinner(""):
        try:
            resp=requests.post(f"{OLLAMA_URL}/api/chat",json=payload,stream=True,timeout=180)
            resp.raise_for_status()
            full=""; ph=st.empty(); cc=0
            for line in resp.iter_lines():
                if not line: continue
                try:
                    c=json.loads(line.decode())
                    tok=c.get("message",{}).get("content","")
                    if tok:
                        full+=tok; cc+=1
                        if cc%25==0: ph.markdown(f'<div class="nf-streaming">{full}▌</div>',unsafe_allow_html=True)
                    if c.get("done"): break
                except: continue
            ph.empty()
            st.session_state.workshop_result=full
            st.session_state.workshop_type=result_type
            st.rerun()
        except Exception as e: st.error(f"Error: {e}")

def load_history_entry(entry):
    st.session_state.story_blocks=entry.get("story_blocks",[])
    st.session_state.book_passage_indices=entry.get("book_passage_indices",[])
    st.session_state.story_title=entry.get("title","Untitled Manuscript")
    st.session_state.word_count=entry.get("word_count",0)
    st.session_state.genre=entry.get("genre","Fantasy")
    st.session_state.tone=entry.get("tone","Cinematic")
    st.session_state.chapter=entry.get("chapter",1)
    st.session_state.characters=entry.get("characters",[])
    st.session_state.story_context=entry.get("story_context","")
    st.session_state.pov=entry.get("pov","Third Person")
    st.session_state.session_id=entry.get("session_id",secrets.token_hex(8))
    st.session_state.session_words=0
    st.session_state.active_tab="forge"

def render_login():
    _,col,_=st.columns([1,1.1,1])
    with col:
        st.markdown('<div class="login-wrap"><div class="login-logo">INKFORGE</div><div class="login-sub">AI Story Co-Writer</div></div>',unsafe_allow_html=True)
        tab_li,tab_reg=st.tabs(["Sign In","Create Account"])
        with tab_li:
            st.markdown("<div style='height:6px'></div>",unsafe_allow_html=True)
            uname=st.text_input("Username",key="li_u",placeholder="username")
            pwd=st.text_input("Password",key="li_p",type="password",placeholder="••••••••")
            if st.button("SIGN IN",use_container_width=True,key="li_btn"):
                if uname and pwd:
                    ok,result,_=login_user(uname,pwd)
                    if ok: st.session_state.auth_token=result; st.rerun()
                    else: st.error(result)
                else: st.warning("Enter username and password.")
            st.markdown('<div class="login-divider"><div class="login-divider-line"></div><div class="login-divider-text">OR</div><div class="login-divider-line"></div></div>',unsafe_allow_html=True)
            if st.button("🔵  Continue with Google",use_container_width=True,key="li_g"):
                st.info("Add your Google OAuth Client ID to enable.")
        with tab_reg:
            st.markdown("<div style='height:6px'></div>",unsafe_allow_html=True)
            disp=st.text_input("Display Name",key="rg_d",placeholder="Your Name")
            runame=st.text_input("Username",key="rg_u",placeholder="choose a username")
            rpwd=st.text_input("Password",key="rg_p",type="password",placeholder="min. 6 chars")
            rpwd2=st.text_input("Confirm",key="rg_p2",type="password",placeholder="repeat")
            if st.button("CREATE ACCOUNT",use_container_width=True,key="rg_btn"):
                if rpwd!=rpwd2: st.error("Passwords don't match.")
                elif runame and rpwd:
                    ok,msg=register_user(runame,rpwd,disp)
                    if ok:
                        ok2,token,_=login_user(runame,rpwd)
                        if ok2: st.session_state.auth_token=token; st.rerun()
                    else: st.error(msg)
                else: st.warning("Fill in all fields.")

user=get_current_user()
if not user: render_login(); st.stop()
username=user["username"]
display=user.get("display_name",username)
avatar=user.get("avatar",username[0].upper())

with st.sidebar:
    st.markdown(f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid #e2dbd0"><div class="nf-avatar">{avatar}</div><div><div style="font-family:\'Playfair Display\',serif;font-size:14px;font-weight:700;color:#111008">{display}</div><div style="font-family:\'Space Mono\',monospace;font-size:8px;color:#8a8470;letter-spacing:.1em">@{username}</div></div></div>',unsafe_allow_html=True)
    if st.button("✦  NEW STORY",use_container_width=True,key="sb_new"):
        for k,v in story_defaults().items(): st.session_state[k]=v
        st.session_state["book_passage_indices"] = []
        st.rerun()

    # ── Search bar ─────────────────────────────────────────────────
    search_q = st.text_input("", placeholder="Search stories…",
                             label_visibility="collapsed", key="sb_search")

    st.markdown('<div class="nf-hist-label">STORY HISTORY</div>', unsafe_allow_html=True)

    for _k in ("menu_sid","rename_sid","rename_val","share_url_show"):
        if _k not in st.session_state: st.session_state[_k] = ""

    # ── Handle query param actions from popup menu ─────────────────
    qp = st.query_params
    if "nf_action" in qp and "nf_sid" in qp:
        _act = qp["nf_action"]; _asid = qp["nf_sid"]
        st.query_params.clear()
        if _act == "delete":
            delete_history_entry(username, _asid)
            st.session_state.menu_sid = ""
            st.rerun()
        elif _act == "pin":
            pin_history_entry(username, _asid)
            st.session_state.menu_sid = ""
            st.rerun()
        elif _act == "archive":
            archive_history_entry(username, _asid)
            st.session_state.menu_sid = ""
            st.rerun()
        elif _act == "rename":
            _h2 = load_history(username)
            _e2 = next((e for e in _h2 if e.get("session_id")==_asid), {})
            st.session_state.rename_sid = _asid
            st.session_state.rename_val = _e2.get("title","")
            st.session_state.menu_sid = ""
            st.rerun()
        elif _act == "share":
            st.session_state.menu_sid = _asid
            st.session_state.share_url_show = _asid
            st.rerun()

    history = load_history(username)
    if search_q:
        sq = search_q.lower().strip()
        history = [h for h in history if sq in h.get("title","").lower() or sq in h.get("genre","").lower()]

    active_entries   = [h for h in history if not h.get("archived")]
    archived_entries = [h for h in history if h.get("archived")]

    def render_card(entry, username):
        sid      = entry.get("session_id","")
        wc       = entry.get("word_count", 0)
        raw_date = entry.get("updated_at","")[:10]
        try:
            _d  = datetime.strptime(raw_date, "%Y-%m-%d")
            upd = _d.strftime("%d ") + _d.strftime("%b").upper() + _d.strftime(" '%y")
        except: upd = raw_date
        genre    = entry.get("genre","")
        title    = entry.get("title","Untitled")
        pinned   = entry.get("pinned", False)
        archived = entry.get("archived", False)
        active   = (sid == st.session_state.get("session_id",""))
        border   = "#b8860b" if active else ("#7b9eb8" if pinned else "#c5bdb0")
        pin_icon = " 📌" if pinned else ""

        share_token = generate_share_token(username, sid)
        share_url   = f"http://localhost:8501/?share={share_token}"

        # Inline rename — use st.form so Enter key submits
        if st.session_state.rename_sid == sid:
            with st.form(key=f"rnm_form_{sid}"):
                new_name = st.text_input("", value=st.session_state.rename_val,
                                         label_visibility="collapsed")
                rc1, rc2 = st.columns(2)
                with rc1:
                    save = st.form_submit_button("✓ Save", use_container_width=True)
                with rc2:
                    cancel = st.form_submit_button("✕ Cancel", use_container_width=True)
            if save and new_name.strip():
                rename_history_entry(username, sid, new_name.strip())
                st.session_state.rename_sid = ""
                st.rerun()
            elif cancel:
                st.session_state.rename_sid = ""
                st.rerun()
            return

        # Card + dot
        border_col = "#b8860b" if active else ("#7b9eb8" if pinned else "#c5bdb0")
        col_card, col_dot = st.columns([11, 1])
        with col_card:
            st.markdown(f'''<div class="nf-card-wrap" style="border-left-color:{border_col}">
  <div class="nf-card-title-txt">{title}{pin_icon}</div>
  <div class="nf-card-meta-txt">{genre} &middot; {wc:,}w &middot; {upd}</div>
</div>''', unsafe_allow_html=True)
            if st.button("·", key=f"ho_{sid}", use_container_width=True):
                if sid != st.session_state.get("session_id"):  # never reload the already-active session
                    load_history_entry(entry); st.rerun()
        with col_dot:
            menu_open = st.session_state.get("menu_sid") == sid
            if st.button("⋯", key=f"dot_{sid}"):
                st.session_state.menu_sid = "" if menu_open else sid
                st.rerun()

        # Inline menu — stacked compact buttons
        if st.session_state.get("menu_sid") == sid:
            pin_lbl = "Unpin story" if pinned else "Pin story"
            arc_lbl = "Unarchive"   if archived else "Archive"
            st.markdown('<div class="nf-menu-box">', unsafe_allow_html=True)
            if st.button(f"↑  Share",      key=f"msh_{sid}", use_container_width=True):
                st.session_state.share_url_show = sid; st.rerun()
            if st.button(f"✎  Rename",     key=f"mrn_{sid}", use_container_width=True):
                st.session_state.rename_sid = sid
                st.session_state.rename_val = title
                st.session_state.menu_sid   = ""
                st.rerun()
            if st.button(f"⊙  {pin_lbl}", key=f"mpi_{sid}", use_container_width=True):
                pin_history_entry(username, sid)
                st.session_state.menu_sid = ""; st.rerun()
            if st.button(f"▣  {arc_lbl}", key=f"mar_{sid}", use_container_width=True):
                archive_history_entry(username, sid)
                st.session_state.menu_sid = ""; st.rerun()
            if st.button(f"🗑  Delete",    key=f"mde_{sid}", use_container_width=True):
                delete_history_entry(username, sid)
                st.session_state.menu_sid = ""; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            if st.session_state.get("share_url_show") == sid:
                st.code(share_url, language=None)

    if not active_entries and not archived_entries:
        st.markdown('<div style="font-family:\'Crimson Pro\',serif;font-size:13px;font-style:italic;color:#8a8470;text-align:center;padding:16px 0">No stories found.</div>', unsafe_allow_html=True)

    for entry in active_entries:
        render_card(entry, username)

    if archived_entries:
        st.markdown('<div class="nf-hist-label" style="margin-top:14px">ARCHIVED</div>', unsafe_allow_html=True)
        for entry in archived_entries:
            render_card(entry, username)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    if st.button("SIGN OUT", use_container_width=True, key="sb_lo"):
        logout(st.session_state.auth_token); st.session_state.auth_token=""; st.rerun()

pct=min(100,int(st.session_state.get("daily_words",0)/max(st.session_state.writing_goal,1)*100))
st.markdown(f'<div class="nf-nav"><div class="nf-brand"><div class="nf-brand-mark">I</div><div><div class="nf-brand-name">INKFORGE</div><div class="nf-brand-sub">Story Intelligence Engine</div></div></div><div class="nf-pills"><span>{st.session_state.genre}</span><span>{st.session_state.tone}</span><span>{st.session_state.pov}</span><span>{st.session_state.mood}</span></div><div class="nf-nav-right"><div class="nf-progress"><div class="nf-progress-bar"><div class="nf-progress-fill" style="width:{pct}%"></div></div><div class="nf-progress-lbl">{st.session_state.session_words:,} / {st.session_state.writing_goal:,} words today</div></div><div><div class="nf-wc-num">{st.session_state.word_count:,}</div><div class="nf-wc-lbl">total words</div></div></div></div>',unsafe_allow_html=True)

# Tab buttons styled via key prefix in CSS
st.markdown('<div class="nf-tab-bar">', unsafe_allow_html=True)
tc=st.columns(4)
for col,(lbl,key) in zip(tc,[("THE FORGE","forge"),("WORKSHOP","workshop"),("STORY VAULT","vault"),("STORY COMPASS","compass")]):
    with col:
        if st.button(lbl,key=f"nftab_{key}",use_container_width=True):
            st.session_state.active_tab=key; st.rerun()
st.markdown('</div>', unsafe_allow_html=True)
inject_tab_css(st.session_state.active_tab)
st.markdown('<div class="nf-tab-rule"></div>',unsafe_allow_html=True)

if st.session_state.active_tab=="forge":
    genres=["Fantasy","Sci-Fi","Thriller","Romance","Horror","Mystery","Historical","Literary"]
    tones=["Cinematic","Lyrical","Dark & Gritty","Whimsical","Epic","Intimate"]
    povs=["First Person","Third Person","Third Omniscient","Second Person"]

    # Config strip — NO Ollama URL column, FORGE/TEST horizontal
    cs=st.columns([1.5,1.3,1.3,2.2,1.8,0.65])
    with cs[0]: st.selectbox("GENRE",genres,key="genre")
    with cs[1]: st.selectbox("TONE",tones,key="tone")
    with cs[2]: st.selectbox("POV",povs,key="pov")
    with cs[3]:
        title_val = st.text_input("TITLE", value=st.session_state.story_title, label_visibility="visible")
        if title_val != st.session_state.story_title:
            st.session_state.story_title = title_val
    with cs[4]:
        models=get_models()
        if models:
            # Default to llama3 if available, else first model
            _pref = next((m for m in models if m.startswith("llama3")), models[0])
            _cur  = st.session_state.get("ollama_model", _pref)
            idx   = models.index(_cur) if _cur in models else models.index(_pref)
            st.selectbox("MODEL",models,index=idx,key="ollama_model")
        else:
            st.text_input("MODEL",key="ollama_model")
    with cs[5]:
        st.markdown("<div style='height:28px'></div>",unsafe_allow_html=True)
        if st.button("TEST",use_container_width=True,key="tconn"):
            try:
                r=requests.get(f"{OLLAMA_URL}/api/tags",timeout=5)
                n=len(r.json().get("models",[])) if r.status_code==200 else 0
                st.success(f"✓{n}")
            except: st.error("✗")

    st.markdown("<div style='height:4px'></div>",unsafe_allow_html=True)
    left,center,right=st.columns([1,3.5,1.2])

    with left:
        # CSS class applied via container key trick — no orphaned divs
        left_panel = st.container()
        with left_panel:
            st.markdown('<p class="nf-panel-title">ACTIONS</p>',unsafe_allow_html=True)
            selected_action=None
            for lbl,akey in [
                ("CONTINUE","continue"),
                ("ENHANCE","enhance"),
                ("REWRITE","rewrite"),
                ("PLOT TWIST","twist"),
                ("DIALOGUE","dialogue"),
                ("DESCRIBE","describe"),
                ("FORESHADOW","foreshadow"),
                ("RAISE STAKES","stakes"),
                ("FLASHBACK","flashback"),
                ("END CHAPTER","chapter_end"),
            ]:
                if st.button(lbl,key=f"a_{akey}",use_container_width=True):
                    selected_action=akey
            st.markdown('<hr style="border:none;border-top:1px solid #e2dbd0;margin:12px 0">',unsafe_allow_html=True)
            st.markdown('<p class="nf-panel-title">SCENE MOOD</p>',unsafe_allow_html=True)
            st.radio("mood",["Neutral","Tense","Melancholic","Hopeful","Foreboding","Magical","Intense","Serene"],label_visibility="collapsed",key="mood")
            st.markdown('<hr style="border:none;border-top:1px solid #e2dbd0;margin:12px 0">',unsafe_allow_html=True)
            st.markdown('<p class="nf-panel-title">DAILY GOAL</p>',unsafe_allow_html=True)
            new_goal = st.number_input("goal",min_value=100,max_value=10000,step=100,label_visibility="collapsed",value=st.session_state.writing_goal)
            if new_goal != st.session_state.writing_goal:
                st.session_state.writing_goal = new_goal
                st.rerun()
            pct2=min(100,int(st.session_state.get("daily_words",0)/max(st.session_state.writing_goal,1)*100))
            st.markdown(f'<div class="nf-goal-track"><div class="nf-goal-fill" style="width:{pct2}%"></div></div><div class="nf-goal-label">{st.session_state.session_words:,} of {st.session_state.writing_goal:,} words</div>',unsafe_allow_html=True)

    with center:
        st.markdown('<div class="nf-book-label">YOUR MANUSCRIPT</div>',unsafe_allow_html=True)
        render_book(st.session_state.story_blocks,st.session_state.book_passage_indices,
                    st.session_state.story_title,st.session_state.genre,
                    st.session_state.chapter,st.session_state.word_count)
        if st.session_state.book_passage_indices:
            bc1,bc2,bc3=st.columns(3)
            with bc1:
                pdf_bytes = generate_book_pdf(
                    st.session_state.story_blocks,
                    st.session_state.book_passage_indices,
                    st.session_state.story_title,
                    genre=st.session_state.genre,
                    tone=st.session_state.tone)
                fname = f"{st.session_state.story_title.replace(' ','_')}_book.pdf"
                st.download_button("DOWNLOAD BOOK", pdf_bytes, file_name=fname,
                                   mime="application/pdf", use_container_width=True)
            with bc2:
                if st.button("NEW CHAPTER",key="nch",use_container_width=True):
                    st.session_state.chapter+=1
                    st.session_state.story_blocks.append({"type":"chapter_break","content":f"Chapter {st.session_state.chapter}","timestamp":datetime.now().strftime("%H:%M"),"chapter_at_time":st.session_state.chapter})
                    st.rerun()
            with bc3:
                if st.button("CLEAR BOOK",key="clrbook",use_container_width=True):
                    st.session_state.book_passage_indices=[]; st.rerun()

        st.markdown('<div class="nf-book-label">STORY FEED</div>',unsafe_allow_html=True)
        if st.session_state.story_title!="Untitled Manuscript":
            st.markdown(f'<div class="nf-ms-head"><div class="nf-ms-rule"><div class="nf-ms-rule-line"></div><div class="nf-ms-rule-glyph">* * *</div><div class="nf-ms-rule-line"></div></div><div class="nf-ms-chapter">Chapter {st.session_state.chapter}</div><div class="nf-ms-title">{st.session_state.story_title}</div><div class="nf-ms-meta">{st.session_state.genre} · {st.session_state.tone} · {st.session_state.pov}</div><div class="nf-ms-rule" style="margin-top:10px"><div class="nf-ms-rule-line"></div><div class="nf-ms-rule-glyph">* * *</div><div class="nf-ms-rule-line"></div></div></div>',unsafe_allow_html=True)
        if not st.session_state.story_blocks: render_empty_state()
        else:
            for i,block in enumerate(st.session_state.story_blocks):
                render_story_block(block,i,on_book_saved=auto_save)

        st.markdown('<div class="nf-write-zone">',unsafe_allow_html=True)
        ic, sc = st.columns([7, 1.5])
        with ic:
            user_input = st.text_area("inp", placeholder="Write your next direction, a line, an idea…",
                                      height=84, key="main_in", label_visibility="collapsed")
        with sc:
            st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
            st.markdown('<div class="nf-forge-btn">', unsafe_allow_html=True)
            send = st.button("FORGE", key="forge_go", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        right_panel = st.container()
        with right_panel:
            # ── CHARACTERS ──────────────────────────────────────────
            char_label = 'CHARACTERS <span style="font-size:7px;letter-spacing:.08em;color:#2a7a4b;font-family:var(--fu);margin-left:6px">✦ SET</span>' if st.session_state.characters else 'CHARACTERS'
            st.markdown('<p style="font-size:10px;color:#9a9080;margin:-6px 0 4px;font-family:var(--fu)">Type your characters — the AI will use them in every passage.</p>', unsafe_allow_html=True)
            char_raw = st.text_area("chars",
                value="\n".join(st.session_state.characters),
                placeholder="Arjun — a fearless detective\nPriya — his sharp-witted partner\nVikram — the mysterious informant",
                height=100, label_visibility="collapsed")
            if char_raw is not None:
                new_chars = [x.strip() for x in char_raw.strip().split("\n") if x.strip()]
                if new_chars != st.session_state.characters:
                    st.session_state.characters = new_chars
            if st.session_state.characters:
                if st.button("✕ CLEAR", key="clr_chars", use_container_width=True):
                    st.session_state.characters = []
                    st.rerun()
            st.markdown('<hr style="border:none;border-top:1px solid #e2dbd0;margin:12px 0">',unsafe_allow_html=True)

            # ── WORLD / CONTEXT ─────────────────────────────────────
            world_label = 'WORLD / CONTEXT <span style="font-size:7px;letter-spacing:.08em;color:#2a7a4b;font-family:var(--fu);margin-left:6px">✦ SET</span>' if st.session_state.story_context.strip() else 'WORLD / CONTEXT'
            st.markdown('<p style="font-size:10px;color:#9a9080;margin:-6px 0 4px;font-family:var(--fu)">Describe your world — setting, rules, era. AI follows this strictly.</p>', unsafe_allow_html=True)
            new_context = st.text_area("world",
                value=st.session_state.story_context,
                placeholder="Set in 1920s Chennai.\nMagic is forbidden by the British Raj.\nOnly women can wield it.",
                height=90, label_visibility="collapsed")
            if new_context != st.session_state.story_context:
                st.session_state.story_context = new_context
            if st.session_state.story_context.strip():
                if st.button("✕ CLEAR", key="clr_ctx", use_container_width=True):
                    st.session_state.story_context = ""
                    st.rerun()
            st.markdown('<hr style="border:none;border-top:1px solid #e2dbd0;margin:12px 0">',unsafe_allow_html=True)
            st.markdown('<p class="nf-panel-title">AUTHOR FIXES</p>',unsafe_allow_html=True)
            for lbl,fkey in [("OVERCOME BLOCK","overcome_block"),("FIX PACING","fix_pacing"),("ADD TENSION","add_tension"),("ADD SPECIFICS","add_specifics"),("DEEPEN EMOTION","deepen_emotion"),("VARY STYLE","vary_style")]:
                if st.button(lbl,key=f"fx_{fkey}",use_container_width=True):
                    st.session_state["pending_fix"] = fkey
            st.markdown('<hr style="border:none;border-top:1px solid #e2dbd0;margin:12px 0">',unsafe_allow_html=True)
            st.markdown('<p class="nf-panel-title">STATISTICS</p>',unsafe_allow_html=True)
            sp=len([b for b in st.session_state.story_blocks if b["type"]=="story"])
            bk=len(st.session_state.book_passage_indices)
            st.markdown(f'<div class="nf-stats-grid"><div class="nf-stat"><div class="nf-stat-n">{st.session_state.word_count:,}</div><div class="nf-stat-l">Words</div></div><div class="nf-stat"><div class="nf-stat-n">{max(1,st.session_state.word_count//200)}m</div><div class="nf-stat-l">Read</div></div><div class="nf-stat"><div class="nf-stat-n">{sp}</div><div class="nf-stat-l">Passages</div></div><div class="nf-stat"><div class="nf-stat-n">{bk}</div><div class="nf-stat-l">In Book</div></div></div>',unsafe_allow_html=True)

    fix_map={"overcome_block":"__Give me 5 specific directions this story could take next.",
        "fix_pacing":"__Rewrite last passage with better pacing — vary sentence lengths.",
        "add_tension":"__Rewrite to inject conflict. Something must feel at risk.",
        "add_specifics":"__Rewrite with hyper-specific sensory detail.",
        "deepen_emotion":"__Rewrite to show the character's interior world more vividly.",
        "vary_style":"__Rewrite alternating short punchy with long flowing sentences."}
    action_map={"continue":"__Continue the narrative naturally.",
        "enhance":"__Elevate the prose quality of the last passage.",
        "rewrite":"__Reimagine the last passage from a fresh angle.",
        "twist":"__Inject a surprising organic plot twist.",
        "dialogue":"__Add a subtext-rich dialogue scene.",
        "describe":"__Write a rich sensory description of the current scene.",
        "foreshadow":"__Continue while subtly foreshadowing a future event.",
        "stakes":"__Continue and raise the stakes dramatically.",
        "flashback":"__Insert a brief revealing flashback.",
        "chapter_end":"__Write a powerful chapter ending with a hook."}
    if send and user_input.strip(): process_story(user_input.strip(),"continue")
    elif selected_action and st.session_state.story_blocks: process_story(action_map.get(selected_action,f"__{selected_action}"),selected_action)
    elif selected_action: st.warning("Write your opening first.")
    elif st.session_state.get("pending_fix") and st.session_state.story_blocks:
        _fix = st.session_state.pop("pending_fix")
        process_story(fix_map.get(_fix, f"__{_fix}"), _fix)
    elif st.session_state.get("pending_fix"):
        st.session_state.pop("pending_fix")
        st.warning("Write something first.")

elif st.session_state.active_tab=="workshop":
    st.markdown("""<style>
/* Workshop tab — all wk_ buttons: white bg, black text, invert on hover */
[data-testid="stHorizontalBlock"] [data-testid="stVerticalBlock"] .stButton > button {
  background: #fff !important;
  border: 1.5px solid #111008 !important;
  color: #111008 !important;
}
[data-testid="stHorizontalBlock"] [data-testid="stVerticalBlock"] .stButton > button * {
  color: #111008 !important;
  -webkit-text-fill-color: #111008 !important;
}
[data-testid="stHorizontalBlock"] [data-testid="stVerticalBlock"] .stButton > button:hover {
  background: #111008 !important;
  border-color: #111008 !important;
}
[data-testid="stHorizontalBlock"] [data-testid="stVerticalBlock"] .stButton > button:hover * {
  color: #fff !important;
  -webkit-text-fill-color: #fff !important;
}
</style>""", unsafe_allow_html=True)
    st.markdown('<div class="nf-section-head"><div class="nf-section-title">The Author\'s Workshop</div><div class="nf-section-sub">Professional tools for every writing challenge</div></div>',unsafe_allow_html=True)
    r1c1,r1c2,r1c3=st.columns(3)
    with r1c1:
        st.markdown('<div class="nf-wcard"><div class="nf-wcard-title">Character Forge</div><div class="nf-wcard-sub">Build psychologically deep characters</div>',unsafe_allow_html=True)
        cname=st.text_input("Name",placeholder="Elena Voss",key="wk_cn")
        crole=st.selectbox("Role",["Protagonist","Antagonist","Mentor","Love Interest","Foil","Mysterious Figure"],key="wk_cr")
        ctrait=st.text_area("Traits",placeholder="Brilliant but broken.",height=52,key="wk_ct")
        st.markdown('<div class="nf-wbtn"></div>', unsafe_allow_html=True)
        if st.button("GENERATE CHARACTER",use_container_width=True,key="wk_cbtn") and cname:
            workshop_query(f"Deep character profile for '{cname}', a {crole} in {st.session_state.genre}. Traits: {ctrait}. Include backstory, motivation, fear, secret, contradiction, speech pattern.","Character Profile")
        st.markdown('</div>',unsafe_allow_html=True)
    with r1c2:
        st.markdown('<div class="nf-wcard"><div class="nf-wcard-title">World Architect</div><div class="nf-wcard-sub">Build immersive fictional worlds</div>',unsafe_allow_html=True)
        wtype=st.selectbox("World Type",["Medieval Fantasy","Dystopian Future","Victorian","Modern Urban","Space Opera","Post-Apocalyptic"],key="wk_wt")
        wconcept=st.text_area("Core concept",placeholder="Magic powered by memories.",height=52,key="wk_wc")
        st.markdown('<style>.nf-wb-wrap .stButton>button{background:#fff!important;border:1.5px solid #111008!important;color:#111008!important}.nf-wb-wrap .stButton>button *{color:#111008!important;-webkit-text-fill-color:#111008!important}.nf-wb-wrap .stButton>button:hover{background:#111008!important;border-color:#111008!important}.nf-wb-wrap .stButton>button:hover *{color:#fff!important;-webkit-text-fill-color:#fff!important}</style>', unsafe_allow_html=True)
        with st.container():
            st.markdown('<div class="nf-wb-wrap">', unsafe_allow_html=True)
            if st.button("BUILD WORLD BIBLE",use_container_width=True,key="wk_wbtn"):
                workshop_query(f"World bible for {wtype}. Concept: {wconcept}. Include power systems, social structure, locations, history.","World Bible")
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
    with r1c3:
        st.markdown('<div class="nf-wcard"><div class="nf-wcard-title">Plot Architect</div><div class="nf-wcard-sub">Structure with narrative frameworks</div>',unsafe_allow_html=True)
        pconcept=st.text_area("Premise",placeholder="A disgraced detective must solve her own ruin.",height=52,key="wk_pc")
        pstruct=st.selectbox("Structure",["Three Act","Hero's Journey","Save the Cat","Five Act","Kishōtenketsu"],key="wk_ps")
        st.markdown('<div class="nf-wbtn"></div>', unsafe_allow_html=True)
        if st.button("GENERATE OUTLINE",use_container_width=True,key="wk_pbtn") and pconcept:
            workshop_query(f"{pstruct} outline for: {pconcept}. Genre: {st.session_state.genre}.","Story Outline")
        st.markdown('</div>',unsafe_allow_html=True)
    r2c1,r2c2,r2c3=st.columns(3)
    with r2c1:
        st.markdown('<div class="nf-wcard"><div class="nf-wcard-title">Dialogue Coach</div><div class="nf-wcard-sub">Rewrite with subtext</div>',unsafe_allow_html=True)
        wdial=st.text_area("Paste dialogue",height=68,key="wk_dl")
        st.markdown('<div class="nf-wbtn"></div>', unsafe_allow_html=True)
        if st.button("REWRITE WITH SUBTEXT",use_container_width=True,key="wk_dbtn") and wdial:
            workshop_query(f"Rewrite with subtext for {st.session_state.genre}:\n\n{wdial}","Dialogue Rewrite")
        st.markdown('</div>',unsafe_allow_html=True)
    with r2c2:
        st.markdown('<div class="nf-wcard"><div class="nf-wcard-title">Prose Doctor</div><div class="nf-wcard-sub">Diagnose and elevate writing</div>',unsafe_allow_html=True)
        wprse=st.text_area("Paste passage",height=68,key="wk_pr")
        st.markdown('<style>.nf-pd-wrap .stButton>button{background:#fff!important;border:1.5px solid #111008!important;color:#111008!important}.nf-pd-wrap .stButton>button *{color:#111008!important;-webkit-text-fill-color:#111008!important}.nf-pd-wrap .stButton>button:hover{background:#111008!important;border-color:#111008!important}.nf-pd-wrap .stButton>button:hover *{color:#fff!important;-webkit-text-fill-color:#fff!important}</style>', unsafe_allow_html=True)
        with st.container():
            st.markdown('<div class="nf-pd-wrap">', unsafe_allow_html=True)
            if st.button("DIAGNOSE + REWRITE",use_container_width=True,key="wk_prbtn") and wprse:
                workshop_query(f"Diagnose weaknesses then rewrite as master author:\n\n{wprse}","Prose Diagnosis")
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
    with r2c3:
        st.markdown('<div class="nf-wcard"><div class="nf-wcard-title">Story Analyst</div><div class="nf-wcard-sub">Editorial feedback</div>',unsafe_allow_html=True)
        wtxt=st.text_area("Paste excerpt",height=46,key="wk_an")
        watype=st.selectbox("Focus",["Overall Quality","Pacing","Voice","Show vs Tell","Tension"],key="wk_at")
        st.markdown('<div class="nf-wbtn"></div>', unsafe_allow_html=True)
        if st.button("ANALYSE",use_container_width=True,key="wk_anbtn") and wtxt:
            workshop_query(f"Editorial analysis — {watype}:\n\n{wtxt}","Story Analysis")
        st.markdown('</div>',unsafe_allow_html=True)
    if st.session_state.workshop_result:
        st.markdown(f'<div class="nf-wout"><div class="nf-wout-label">{st.session_state.workshop_type}</div><div class="nf-wout-text">{st.session_state.workshop_result}</div></div>',unsafe_allow_html=True)
        wc1,wc2=st.columns(2)
        with wc1:
            if st.button("ADD TO CONTEXT",use_container_width=True): st.session_state.story_context+="\n"+st.session_state.workshop_result[:400]; st.success("Added.")
        with wc2:
            if st.button("CLEAR",use_container_width=True,key="wclr"): st.session_state.workshop_result=""; st.rerun()

elif st.session_state.active_tab=="vault":
    st.markdown('<div class="nf-section-head"><div class="nf-section-title">The Story Vault</div><div class="nf-section-sub">Export and manage your manuscript</div></div>',unsafe_allow_html=True)
    vc1,vc2=st.columns([2.3,1])
    with vc1:
        st.markdown(f'<div class="nf-vault"><div class="nf-vault-title">{st.session_state.story_title}</div><div class="nf-vault-meta">{st.session_state.genre} · {st.session_state.tone} · {st.session_state.pov} · Ch.{st.session_state.chapter} · {st.session_state.word_count:,} words</div>',unsafe_allow_html=True)
        if st.session_state.story_blocks: st.text_area("",value=engine.compile_story(st.session_state.story_blocks),height=360,label_visibility="collapsed",key="vault_prev")
        else: st.markdown('<div class="nf-vault-empty">No story yet. Head to The Forge.</div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)
    with vc2:
        st.markdown('<div class="nf-panel"><div class="nf-panel-title">EXPORT</div>',unsafe_allow_html=True)
        if st.session_state.story_blocks:
            fname=st.session_state.story_title.replace(" ","_")
            st.download_button("FULL STORY .TXT",engine.compile_story(st.session_state.story_blocks),file_name=f"{fname}.txt",use_container_width=True)
            if st.session_state.book_passage_indices:
                st.download_button("BOOK ONLY .TXT",render_book_export(st.session_state.story_blocks,st.session_state.book_passage_indices,st.session_state.story_title),file_name=f"{fname}_book.txt",use_container_width=True)
        st.markdown('<div class="nf-divider"></div>',unsafe_allow_html=True)
        st.markdown('<div class="nf-panel-title">MANAGE</div>',unsafe_allow_html=True)
        if st.button("CLEAR STORY",use_container_width=True,key="vclear"):
            for k,v in story_defaults().items(): st.session_state[k]=v
            st.rerun()
        st.markdown('</div>',unsafe_allow_html=True)

elif st.session_state.active_tab=="compass":
    st.markdown('<div class="nf-section-head"><div class="nf-section-title">The Story Compass</div><div class="nf-section-sub">Your personal writing coach.</div></div>',unsafe_allow_html=True)
    cc1,cc2=st.columns([2.3,1])
    with cc1:
        cq=st.text_area("Q",placeholder="Why does my protagonist feel flat?",height=100,label_visibility="collapsed",key="compass_q")
        if st.button("GET GUIDANCE",use_container_width=True,key="compass_go") and cq:
            workshop_query(f"Master writing coach. Genre: {st.session_state.genre}.\nQuestion: {cq}","Compass Guidance")
        if st.session_state.workshop_result:
            st.markdown(f'<div class="nf-wout"><div class="nf-wout-label">{st.session_state.workshop_type}</div><div class="nf-wout-text">{st.session_state.workshop_result}</div></div>',unsafe_allow_html=True)
    with cc2:
        st.markdown('<div class="nf-panel"><div class="nf-panel-title">QUICK CRAFT</div>',unsafe_allow_html=True)
        for lbl,query in [
            ("I AM STUCK",f"5 exciting directions my {st.session_state.genre} story could go next."),
            ("PACING GUIDE","Explain pacing control in fiction with examples."),
            ("SUBTEXT","Teach dialogue subtext — characters never say what they mean."),
            ("SHOW DON'T TELL","5 techniques for showing emotion with before/after examples."),
            ("WRITE A VILLAIN","How to write a compelling three-dimensional villain."),
            ("HOOK ENDINGS","6 techniques to end chapters with irresistible hooks."),
            ("OPENING LINES",f"8 stunning opening lines for {st.session_state.genre}."),
            ("RAISE TENSION","7 techniques to build unbearable tension in any scene."),
        ]:
            if st.button(lbl,use_container_width=True,key=f"sc_{lbl[:8]}"): workshop_query(query,"Craft Guidance")
        st.markdown('</div>',unsafe_allow_html=True)
