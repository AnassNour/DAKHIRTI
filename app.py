import streamlit as st
import sqlite3, hashlib, secrets
from datetime import datetime
from contextlib import contextmanager
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="DAKHIRTI", page_icon="💠", layout="wide")
DB_PATH = "dakhirti_web.db"

T = {
"fr": {
"tag":"Votre argent, votre avenir.","login":"Connexion","register":"Créer un compte","user":"Nom d'utilisateur","pw":"Mot de passe","confirm":"Confirmer le mot de passe",
"home":"Tableau de bord","transfer":"Transfert","saving":"Épargne","records":"Revenus & dépenses","history":"Historique","stats":"Analyses","settings":"Paramètres","logout":"Déconnexion",
"balance":"Solde disponible","income":"Revenus","expenses":"Dépenses","recipient":"Nom exact du destinataire","amount":"Montant (DH)","description":"Description / motif","send":"Confirmer le transfert",
"goalname":"Nom de l'objectif","target":"Montant cible (DH)","create":"Créer l'objectif","contribution":"Montant à épargner","addsave":"Ajouter à l'épargne","category":"Catégorie","type":"Type d'opération","expense":"Dépense","revenue":"Revenu","save":"Enregistrer",
"recent":"Opérations récentes","none":"Aucune donnée pour le moment.","success":"Opération effectuée avec succès.","error":"Vérifiez les informations saisies.","low":"Solde insuffisant.","missing":"Destinataire introuvable.","same":"Vous ne pouvez pas vous transférer de l'argent à vous-même.",
"registered":"Compte créé. Connectez-vous.","exists":"Ce nom d'utilisateur existe déjà.","weak":"Le mot de passe doit contenir au moins 8 caractères.","mismatch":"Les mots de passe ne correspondent pas.","bad":"Identifiants incorrects.",
"progress":"Progression des objectifs","overview":"Vue financière","bycat":"Dépenses par catégorie","date":"Date","kind":"Type","details":"Détails","language":"Langue","welcome":"Bienvenue","profile":"Profil","security":"Sécurité","newpw":"Nouveau mot de passe","update":"Mettre à jour","pwok":"Mot de passe mis à jour.",
"emptygoals":"Créez un objectif pour commencer à épargner.","reached":"Objectif atteint !","saved":"Épargné","remaining":"Restant","filter":"Filtrer","demo":"Démo : toutes les sommes sont virtuelles. Aucun transfert bancaire réel.",
"tip":"Astuce : fixez un objectif réaliste et suivez vos dépenses chaque semaine.","created":"Compte créé le","noresult":"Aucune opération ne correspond au filtre.","transfernote":"Le destinataire doit déjà avoir un compte DAKHIRTI.","savingnote":"L'épargne est réservée depuis votre solde disponible.",
"appearance":"Apparence","dark":"Mode sombre","light":"Mode clair","footer":"DAKHIRTI • Projet éducatif • Version 2.0","savedtotal":"Total épargné","deposit":"Ajouter des fonds démo","withdraw":"Retirer des fonds démo"
},
"ar": {
"tag":"فلوسك، مستقبلك.","login":"تسجيل الدخول","register":"إنشاء حساب","user":"اسم المستخدم","pw":"كلمة المرور","confirm":"تأكيد كلمة المرور",
"home":"الرئيسية","transfer":"تحويل الأموال","saving":"التوفير","records":"المداخيل والمصاريف","history":"سجل العمليات","stats":"الإحصائيات","settings":"الإعدادات","logout":"تسجيل الخروج",
"balance":"الرصيد المتوفر","income":"المداخيل","expenses":"المصاريف","recipient":"اسم المستفيد بالضبط","amount":"المبلغ (درهم)","description":"الوصف / السبب","send":"تأكيد التحويل",
"goalname":"اسم الهدف","target":"المبلغ المستهدف (درهم)","create":"إنشاء الهدف","contribution":"المبلغ المراد توفيره","addsave":"إضافة للتوفير","category":"الصنف","type":"نوع العملية","expense":"مصروف","revenue":"مدخول","save":"حفظ العملية",
"recent":"آخر العمليات","none":"لا توجد بيانات حالياً.","success":"تمت العملية بنجاح.","error":"يرجى التأكد من المعلومات المدخلة.","low":"الرصيد غير كافٍ.","missing":"المستفيد غير موجود.","same":"لا يمكنك تحويل الأموال إلى نفسك.",
"registered":"تم إنشاء الحساب. يمكنك تسجيل الدخول.","exists":"اسم المستخدم موجود مسبقاً.","weak":"كلمة المرور يجب أن تتكون من 8 أحرف على الأقل.","mismatch":"كلمتا المرور غير متطابقتين.","bad":"معلومات الدخول غير صحيحة.",
"progress":"تقدم أهداف التوفير","overview":"نظرة مالية عامة","bycat":"المصاريف حسب الصنف","date":"التاريخ","kind":"النوع","details":"التفاصيل","language":"اللغة","welcome":"مرحباً","profile":"الملف الشخصي","security":"الأمان","newpw":"كلمة المرور الجديدة","update":"تحديث","pwok":"تم تحديث كلمة المرور.",
"emptygoals":"أنشئ هدفاً للبدء في التوفير.","reached":"وصلت إلى هدفك!","saved":"تم توفير","remaining":"المتبقي","filter":"تصفية","demo":"نسخة تجريبية: جميع الأموال افتراضية ولا توجد تحويلات بنكية حقيقية.",
"tip":"نصيحة: حدد هدفاً واقعياً وراقب مصاريفك كل أسبوع.","created":"تاريخ إنشاء الحساب","noresult":"لا توجد عمليات تطابق التصفية.","transfernote":"يجب أن يكون المستفيد مسجلاً مسبقاً في DAKHIRTI.","savingnote":"يتم اقتطاع مبلغ التوفير من رصيدك المتاح.",
"appearance":"المظهر","dark":"الوضع الداكن","light":"الوضع الفاتح","footer":"DAKHIRTI • مشروع تعليمي • الإصدار 2.0","savedtotal":"إجمالي التوفير","deposit":"إضافة رصيد تجريبي","withdraw":"سحب رصيد تجريبي"
}}
def tr(k): return T[st.session_state.get("lang","fr")].get(k,k)
def db():
    c=sqlite3.connect(DB_PATH,timeout=20); c.row_factory=sqlite3.Row; c.execute("PRAGMA foreign_keys=ON"); return c
@contextmanager
def txdb():
    c=db()
    try: c.execute("BEGIN IMMEDIATE"); yield c; c.commit()
    except: c.rollback(); raise
    finally: c.close()
def init():
    with db() as c:
        c.executescript("""CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT NOT NULL UNIQUE COLLATE NOCASE,salt TEXT NOT NULL,password_hash TEXT NOT NULL,balance REAL NOT NULL DEFAULT 1000,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS transactions(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL REFERENCES users(id),kind TEXT NOT NULL,amount REAL NOT NULL CHECK(amount>0),category TEXT NOT NULL DEFAULT '',details TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS goals(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL REFERENCES users(id),title TEXT NOT NULL,target REAL NOT NULL CHECK(target>0),saved REAL NOT NULL DEFAULT 0,created_at TEXT NOT NULL);""")
def ph(p,s): return hashlib.pbkdf2_hmac("sha256",p.encode(),s.encode(),240000).hex()
def addtx(c,uid,k,a,cat="",detail=""): c.execute("INSERT INTO transactions(user_id,kind,amount,category,details,created_at) VALUES(?,?,?,?,?,?)",(uid,k,round(float(a),2),cat,detail,datetime.now().isoformat(timespec="seconds")))
def create_user(n,p):
    if len(p)<8:return False,tr("weak")
    s=secrets.token_hex(16)
    try:
        with txdb() as c:c.execute("INSERT INTO users(username,salt,password_hash,balance,created_at) VALUES(?,?,?,?,?)",(n.strip(),s,ph(p,s),1000,datetime.now().isoformat(timespec="seconds")))
        return True,tr("registered")
    except sqlite3.IntegrityError:return False,tr("exists")
def auth(n,p):
    with db() as c:u=c.execute("SELECT * FROM users WHERE username=? COLLATE NOCASE",(n.strip(),)).fetchone()
    return dict(u) if u and ph(p,u["salt"])==u["password_hash"] else None
def data(uid):
    with db() as c:
        u=c.execute("SELECT * FROM users WHERE id=?",(uid,)).fetchone()
        t=pd.read_sql_query("SELECT id,kind,amount,category,details,created_at FROM transactions WHERE user_id=? ORDER BY id DESC",c,params=(uid,))
        g=pd.read_sql_query("SELECT id,title,target,saved,created_at FROM goals WHERE user_id=? ORDER BY id DESC",c,params=(uid,))
    return u,t,g
def fmt(v):return f"{v:,.2f} DH"
def transfer(uid,name,amount,note):
    if amount<=0:return False,tr("error")
    with txdb() as c:
        a=c.execute("SELECT * FROM users WHERE id=?",(uid,)).fetchone(); b=c.execute("SELECT * FROM users WHERE username=? COLLATE NOCASE",(name.strip(),)).fetchone()
        if not b:return False,tr("missing")
        if b["id"]==uid:return False,tr("same")
        if a["balance"]<amount:return False,tr("low")
        c.execute("UPDATE users SET balance=balance-? WHERE id=?",(amount,uid));c.execute("UPDATE users SET balance=balance+? WHERE id=?",(amount,b["id"]))
        addtx(c,uid,"transfer_out",amount,"Transfert",f"Vers {b['username']} — {note}");addtx(c,b["id"],"transfer_in",amount,"Transfert",f"De {a['username']} — {note}")
    return True,tr("success")
def change(uid,a,k):
    if a<=0:return False,tr("error")
    with txdb() as c:
        u=c.execute("SELECT balance FROM users WHERE id=?",(uid,)).fetchone()
        if k=="withdrawal" and u["balance"]<a:return False,tr("low")
        c.execute("UPDATE users SET balance=balance+? WHERE id=?",((a if k=="deposit" else -a),uid));addtx(c,uid,k,a,"Démo","Opération de démonstration")
    return True,tr("success")
def goal(uid,n,t):
    if not n.strip() or t<=0:return False
    with txdb() as c:c.execute("INSERT INTO goals(user_id,title,target,saved,created_at) VALUES(?,?,?,?,?)",(uid,n.strip(),t,0,datetime.now().isoformat(timespec="seconds")))
    return True
def contribute(uid,gid,a):
    if a<=0:return False,tr("error")
    with txdb() as c:
        u=c.execute("SELECT balance FROM users WHERE id=?",(uid,)).fetchone();g=c.execute("SELECT * FROM goals WHERE id=? AND user_id=?",(gid,uid)).fetchone()
        if not g:return False,tr("error")
        if u["balance"]<a:return False,tr("low")
        a=min(a,max(0,g["target"]-g["saved"]))
        if not a:return False,tr("error")
        c.execute("UPDATE users SET balance=balance-? WHERE id=?",(a,uid));c.execute("UPDATE goals SET saved=saved+? WHERE id=?",(a,gid));addtx(c,uid,"saving",a,"Épargne",f"Objectif : {g['title']}")
    return True,tr("success")
def record(uid,k,a,cat,note):
    if a<=0:return False,tr("error")
    with txdb() as c:
        u=c.execute("SELECT balance FROM users WHERE id=?",(uid,)).fetchone()
        if k=="expense" and u["balance"]<a:return False,tr("low")
        c.execute("UPDATE users SET balance=balance+? WHERE id=?",((a if k=="income" else -a),uid));addtx(c,uid,k,a,cat,note)
    return True,tr("success")

def design():
    dark=st.session_state.theme=="dark"; bg="#071522" if dark else "#F2F7FA"; panel="#10283A" if dark else "#FFFFFF"; fg="#EAF4F8" if dark else "#172B3B"; muted="#A5BAC8" if dark else "#63798A"; edge="#29485C" if dark else "#DCE6ED"; accent="#36D6A5"
    st.markdown(f"""<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&family=Inter:wght@400;600;700;800&display=swap');
    .stApp{{background:radial-gradient(circle at 8% 0%,{'#173B50' if dark else '#DFF6EF'} 0%,{bg} 48%);color:{fg};}}
    [data-testid="stSidebar"]{{background:{panel};border-right:1px solid {edge};}}
    html,body,[class*="css"]{{font-family:{'Cairo,sans-serif' if st.session_state.lang=='ar' else 'Inter,sans-serif'};}}
    .block-container{{max-width:1250px;padding-top:1.5rem;padding-bottom:3rem;}}
    .brand{{font-size:39px;font-weight:900;letter-spacing:2px;color:{accent};text-align:center;margin-top:4px;}}
    .tag{{text-align:center;color:{muted};margin-bottom:22px;}}
    .hero{{background:linear-gradient(120deg,{'#123A50' if dark else '#DDF7EF'},{'#15594F' if dark else '#FFFFFF'});border:1px solid {edge};border-radius:22px;padding:22px 26px;margin:12px 0 20px;}}
    .hero small{{color:{muted};}} .hero strong{{display:block;color:{accent};font-size:34px;margin:6px 0;}}
    div[data-testid="stMetric"]{{background:{panel};border:1px solid {edge};padding:16px;border-radius:16px;}}
    div[data-testid="stMetric"] label{{color:{muted}!important;}}
    .stButton>button,.stFormSubmitButton>button{{border-radius:12px;font-weight:700;min-height:42px;}}
    div[data-testid="stExpander"]{{border:1px solid {edge};border-radius:14px;}}
    </style>""",unsafe_allow_html=True)
def brand():st.markdown("<div class='brand'>💠 DAKHIRTI</div>",unsafe_allow_html=True);st.markdown(f"<div class='tag'>{tr('tag')}</div>",unsafe_allow_html=True)
def login():
    brand();_,mid,_=st.columns([1,1.15,1])
    with mid:
        tab1,tab2=st.tabs([tr("login"),tr("register")])
        with tab1:
            with st.form("login"):
                n=st.text_input(tr("user"));p=st.text_input(tr("pw"),type="password");ok=st.form_submit_button(tr("login"),use_container_width=True,type="primary")
            if ok:
                u=auth(n,p)
                if u:st.session_state.uid=u["id"];st.session_state.uname=u["username"];st.rerun()
                else:st.error(tr("bad"))
        with tab2:
            with st.form("register"):
                n=st.text_input(tr("user"),key="newuser");p=st.text_input(tr("pw"),type="password",key="newpw1");p2=st.text_input(tr("confirm"),type="password");ok=st.form_submit_button(tr("register"),use_container_width=True,type="primary")
            if ok:
                if p!=p2:st.error(tr("mismatch"))
                elif not n.strip():st.error(tr("error"))
                else:
                    good,msg=create_user(n,p);(st.success if good else st.error)(msg)
def dashboard(u,t,g):
    st.subheader(f"{tr('welcome')}, {u['username']} 👋")
    st.markdown(f"<div class='hero'><small>{tr('balance')}</small><strong>{fmt(u['balance'])}</strong><small>💠 DAKHIRTI · {tr('demo')}</small></div>",unsafe_allow_html=True)
    inc=t.loc[t.kind.isin(["income","deposit","transfer_in"]),"amount"].sum() if not t.empty else 0
    exp=t.loc[t.kind.isin(["expense","withdrawal","transfer_out","saving"]),"amount"].sum() if not t.empty else 0
    a,b,c=st.columns(3);a.metric("📈 "+tr("income"),fmt(inc));b.metric("📉 "+tr("expenses"),fmt(exp));c.metric("🎯 "+tr("savedtotal"),fmt(g.saved.sum() if not g.empty else 0))
    st.markdown("### "+tr("progress"))
    if g.empty:st.info(tr("emptygoals"))
    else:
        for _,x in g.head(5).iterrows():st.write(f"**{x.title}** · {fmt(x.saved)} / {fmt(x.target)}");st.progress(min(float(x.saved)/float(x.target),1))
    st.markdown("### "+tr("recent"))
    if t.empty:st.info(tr("none"))
    else:
        v=t.head(6).copy();v["amount"]=v.amount.map(fmt);v=v.rename(columns={"kind":tr("kind"),"amount":tr("amount"),"category":tr("category"),"details":tr("details"),"created_at":tr("date")});st.dataframe(v[[tr("date"),tr("kind"),tr("amount"),tr("category"),tr("details")]],use_container_width=True,hide_index=True)
    st.info(tr("tip"))
def transfer_page(u):
    st.subheader("💸 "+tr("transfer"));st.caption(tr("transfernote"))
    with st.form("transfer_form"):
        n=st.text_input(tr("recipient"));a=st.number_input(tr("amount"),min_value=0.0,step=10.0);d=st.text_input(tr("description"));ok=st.form_submit_button(tr("send"),type="primary",use_container_width=True)
    if ok:
        good,msg=transfer(u["id"],n,a,d);(st.success if good else st.error)(msg)
        if good:st.rerun()
    with st.expander(tr("deposit")+" / "+tr("withdraw")):
        x,y=st.columns(2)
        with x:
            with st.form("deposit"):
                a=st.number_input(tr("deposit"),min_value=0.0,step=50.0);ok=st.form_submit_button(tr("deposit"))
            if ok:
                good,msg=change(u["id"],a,"deposit");(st.success if good else st.error)(msg)
                if good:st.rerun()
        with y:
            with st.form("withdraw"):
                a=st.number_input(tr("withdraw"),min_value=0.0,step=50.0);ok=st.form_submit_button(tr("withdraw"))
            if ok:
                good,msg=change(u["id"],a,"withdrawal");(st.success if good else st.error)(msg)
                if good:st.rerun()
def savings_page(u,g):
    st.subheader("🎯 "+tr("saving"));st.caption(tr("savingnote"))
    with st.expander("＋ "+tr("create"),expanded=g.empty):
        with st.form("goalform"):
            n=st.text_input(tr("goalname"));a=st.number_input(tr("target"),min_value=0.0,step=100.0);ok=st.form_submit_button(tr("create"),type="primary")
        if ok:
            if goal(u["id"],n,a):st.success(tr("success"));st.rerun()
            else:st.error(tr("error"))
    for _,x in g.iterrows():
        with st.container(border=True):
            st.markdown("#### 🎯 "+x.title);p=min(float(x.saved)/float(x.target),1);st.progress(p)
            a,b,c=st.columns(3);a.metric(tr("saved"),fmt(x.saved));b.metric(tr("target"),fmt(x.target));c.metric(tr("remaining"),fmt(max(0,x.target-x.saved)))
            if p>=1:st.success(tr("reached"))
            else:
                with st.form(f"goal_{int(x.id)}"):
                    a=st.number_input(tr("contribution"),min_value=0.0,step=10.0,key=f"contrib_{int(x.id)}");ok=st.form_submit_button(tr("addsave"))
                if ok:
                    good,msg=contribute(u["id"],int(x.id),a);(st.success if good else st.error)(msg)
                    if good:st.rerun()
def records_page(u):
    st.subheader("🧾 "+tr("records"))
    with st.form("records"):
        typ=st.radio(tr("type"),[tr("expense"),tr("revenue")],horizontal=True);k="expense" if typ==tr("expense") else "income"
        a=st.number_input(tr("amount"),min_value=0.0,step=10.0);cat=st.selectbox(tr("category"),["Food / أكل","Transport / نقل","Shopping / تسوق","Bills / فواتير","Study / دراسة","Health / صحة","Other / أخرى"]);note=st.text_input(tr("description"));ok=st.form_submit_button(tr("save"),type="primary",use_container_width=True)
    if ok:
        good,msg=record(u["id"],k,a,cat,note);(st.success if good else st.error)(msg)
        if good:st.rerun()
def history_page(t):
    st.subheader("📜 "+tr("history"))
    if t.empty:st.info(tr("none"));return
    kinds=sorted(t.kind.unique().tolist());chosen=st.multiselect(tr("filter"),kinds,default=kinds);v=t[t.kind.isin(chosen)].copy()
    if v.empty:st.info(tr("noresult"));return
    v["amount"]=v.amount.map(fmt);v=v.rename(columns={"kind":tr("kind"),"amount":tr("amount"),"category":tr("category"),"details":tr("details"),"created_at":tr("date")});st.dataframe(v[[tr("date"),tr("kind"),tr("amount"),tr("category"),tr("details")]],use_container_width=True,hide_index=True)
def analytics(t,g):
    st.subheader("📊 "+tr("stats"))
    if t.empty:st.info(tr("none"));return
    d=t.copy();d["created_at"]=pd.to_datetime(d.created_at);d["month"]=d.created_at.dt.strftime("%Y-%m")
    flow=d[d.kind.isin(["income","expense","deposit","withdrawal","transfer_in","transfer_out"])].copy()
    if not flow.empty:
        flow["net"]=flow.apply(lambda r:r.amount if r.kind in ["income","deposit","transfer_in"] else -r.amount,axis=1);ch=flow.groupby("month",as_index=False).net.sum()
        st.markdown("### "+tr("overview"));st.plotly_chart(px.bar(ch,x="month",y="net"),use_container_width=True)
    ex=d[d.kind=="expense"]
    if not ex.empty:st.markdown("### "+tr("bycat"));st.plotly_chart(px.pie(ex.groupby("category",as_index=False).amount.sum(),names="category",values="amount",hole=.55),use_container_width=True)
    if not g.empty:
        gd=g[["title","target","saved"]].melt(id_vars="title",var_name="type",value_name="amount");st.plotly_chart(px.bar(gd,x="title",y="amount",color="type",barmode="group"),use_container_width=True)
def settings_page(u):
    st.subheader("⚙️ "+tr("settings"));st.write(f"**{tr('profile')}:** {u['username']}");st.write(f"**{tr('created')}:** {u['created_at'][:10]}")
    st.markdown("### "+tr("security"))
    with st.form("password"):
        old=st.text_input(tr("pw"),type="password");new=st.text_input(tr("newpw"),type="password");ok=st.form_submit_button(tr("update"))
    if ok:
        if not auth(u["username"],old):st.error(tr("bad"))
        elif len(new)<8:st.error(tr("weak"))
        else:
            s=secrets.token_hex(16)
            with txdb() as c:c.execute("UPDATE users SET salt=?,password_hash=? WHERE id=?",(s,ph(new,s),u["id"]))
            st.success(tr("pwok"))
def main():
    init()
    for k,v in {"lang":"fr","theme":"dark","uid":None}.items():
        if k not in st.session_state:st.session_state[k]=v
    with st.sidebar:
        st.markdown("## 💠 DAKHIRTI");st.caption(tr("tag"))
        lang=st.radio(tr("language"),["Français","العربية"],index=0 if st.session_state.lang=="fr" else 1,horizontal=True)
        st.session_state.lang="fr" if lang=="Français" else "ar"
        st.divider();st.markdown("**"+tr("appearance")+"**")
        mode=st.radio("Theme",[tr("dark"),tr("light")],index=0 if st.session_state.theme=="dark" else 1,horizontal=True,label_visibility="collapsed")
        st.session_state.theme="dark" if mode==tr("dark") else "light"
        st.divider();st.caption(tr("demo"))
        if st.session_state.uid:
            st.write("👤 "+st.session_state.get("uname",""))
            if st.button(tr("logout"),use_container_width=True):st.session_state.uid=None;st.session_state.uname=None;st.rerun()
    design()
    if not st.session_state.uid:login();st.caption(tr("footer"));return
    u,t,g=data(st.session_state.uid)
    if u is None:st.session_state.uid=None;st.rerun()
    brand()
    pages=[tr("home"),tr("transfer"),tr("saving"),tr("records"),tr("history"),tr("stats"),tr("settings")];icons=["🏠","💸","🎯","🧾","📜","📊","⚙️"]
    page=st.radio("Navigation",pages,format_func=lambda x:f"{icons[pages.index(x)]}  {x}",horizontal=True,label_visibility="collapsed")
    st.divider()
    if page==tr("home"):dashboard(u,t,g)
    elif page==tr("transfer"):transfer_page(u)
    elif page==tr("saving"):savings_page(u,g)
    elif page==tr("records"):records_page(u)
    elif page==tr("history"):history_page(t)
    elif page==tr("stats"):analytics(t,g)
    elif page==tr("settings"):settings_page(u)
    st.markdown(f"<div class='tag' style='margin-top:35px'>{tr('footer')}</div>",unsafe_allow_html=True)
if __name__=="__main__":main()
