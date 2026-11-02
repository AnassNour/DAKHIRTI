import streamlit as st
import sqlite3
import hashlib
import secrets
from datetime import datetime, date
from contextlib import contextmanager
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="DAKHIRTI", page_icon="💠", layout="wide", initial_sidebar_state="expanded")

DB_PATH = "dakhirti_web.db"

I18N = {
    "fr": {
        "tagline":"Votre argent, votre avenir.", "login":"Connexion", "register":"Créer un compte",
        "username":"Nom d'utilisateur", "password":"Mot de passe", "confirm_password":"Confirmer le mot de passe",
        "dashboard":"Tableau de bord", "transfer":"Transfert", "savings":"Épargne", "transactions":"Opérations",
        "analytics":"Analyses", "settings":"Paramètres", "logout":"Déconnexion", "balance":"Solde disponible",
        "income":"Revenus", "expenses":"Dépenses", "send_money":"Envoyer de l'argent", "recipient":"Nom exact du destinataire",
        "amount":"Montant (DH)", "description":"Description / motif", "submit_transfer":"Confirmer le transfert",
        "add_money":"Ajouter des fonds démo", "withdraw":"Retirer des fonds démo", "goal_name":"Nom de l'objectif",
        "target":"Montant cible (DH)", "create_goal":"Créer l'objectif", "goal":"Objectif",
        "contribution":"Montant à épargner", "add_savings":"Ajouter à l'épargne", "category":"Catégorie",
        "type":"Type d'opération", "expense":"Dépense", "revenue":"Revenu", "save_record":"Enregistrer",
        "recent":"Opérations récentes", "no_data":"Aucune donnée pour le moment.",
        "success":"Opération effectuée avec succès.", "error":"Vérifiez les informations saisies.",
        "insufficient":"Solde insuffisant.", "recipient_missing":"Destinataire introuvable.",
        "same_user":"Vous ne pouvez pas vous transférer de l'argent à vous-même.",
        "register_ok":"Compte créé. Vous pouvez maintenant vous connecter.",
        "user_exists":"Ce nom d'utilisateur existe déjà.", "weak_password":"Le mot de passe doit contenir au moins 8 caractères.",
        "password_mismatch":"Les mots de passe ne correspondent pas.", "bad_login":"Identifiants incorrects.",
        "demo":"MODE DÉMO : toutes les sommes sont virtuelles.", "goal_progress":"Progression des objectifs",
        "financial_overview":"Vue financière", "amount_spent":"Dépenses par catégorie",
        "transaction_history":"Historique des opérations", "date":"Date", "kind":"Type", "details":"Détails",
        "status":"Statut", "language":"Langue", "french":"Français", "arabic":"العربية",
        "welcome":"Bienvenue", "profile":"Profil", "initial_balance":"Solde démo initial : 1 000 DH",
        "transfer_in":"Transfert reçu", "transfer_out":"Transfert envoyé", "deposit":"Ajout démo",
        "withdrawal":"Retrait démo", "saving":"Épargne", "expense_label":"Dépense", "revenue_label":"Revenu",
        "security":"Sécurité", "change_password":"Changer le mot de passe", "new_password":"Nouveau mot de passe",
        "update_password":"Mettre à jour", "password_updated":"Mot de passe mis à jour.",
        "empty_goals":"Créez un objectif pour commencer à épargner.", "target_reached":"Objectif atteint !",
        "total_saved":"Total épargné", "goal_saved":"Épargné", "remaining":"Restant",
        "all":"Toutes", "filter":"Filtrer", "search":"Rechercher", "demo_warning":"Application scolaire de démonstration — aucun transfert bancaire réel.",
        "tip":"Astuce : programmez un objectif réaliste et suivez vos dépenses chaque semaine.",
        "quick_actions":"Actions rapides", "monthly":"Résumé du mois", "net":"Solde net des opérations",
        "account_created":"Compte créé le", "no_transactions":"Aucune opération ne correspond au filtre.",
        "deposit_amount":"Montant à ajouter", "withdraw_amount":"Montant à retirer", "confirm":"Confirmer",
        "transfer_note":"Le destinataire doit déjà posséder un compte DAKHIRTI.",
        "savings_note":"L'épargne est réservée depuis votre solde disponible.",
        "footer":"DAKHIRTI • Projet éducatif • Version 1.0"
    },
    "ar": {
        "tagline":"فلوسك، مستقبلك.", "login":"تسجيل الدخول", "register":"إنشاء حساب",
        "username":"اسم المستخدم", "password":"كلمة المرور", "confirm_password":"تأكيد كلمة المرور",
        "dashboard":"الرئيسية", "transfer":"تحويل الأموال", "savings":"التوفير", "transactions":"العمليات",
        "analytics":"الإحصائيات", "settings":"الإعدادات", "logout":"تسجيل الخروج", "balance":"الرصيد المتوفر",
        "income":"المداخيل", "expenses":"المصاريف", "send_money":"إرسال الأموال", "recipient":"اسم المستفيد بالضبط",
        "amount":"المبلغ (درهم)", "description":"الوصف / السبب", "submit_transfer":"تأكيد التحويل",
        "add_money":"إضافة رصيد تجريبي", "withdraw":"سحب رصيد تجريبي", "goal_name":"اسم الهدف",
        "target":"المبلغ المستهدف (درهم)", "create_goal":"إنشاء الهدف", "goal":"الهدف",
        "contribution":"المبلغ المراد توفيره", "add_savings":"إضافة للتوفير", "category":"الصنف",
        "type":"نوع العملية", "expense":"مصروف", "revenue":"مدخول", "save_record":"حفظ العملية",
        "recent":"آخر العمليات", "no_data":"لا توجد بيانات حالياً.",
        "success":"تمت العملية بنجاح.", "error":"يرجى التأكد من المعلومات المدخلة.",
        "insufficient":"الرصيد غير كافٍ.", "recipient_missing":"المستفيد غير موجود.",
        "same_user":"لا يمكنك تحويل الأموال إلى نفسك.",
        "register_ok":"تم إنشاء الحساب. يمكنك تسجيل الدخول الآن.",
        "user_exists":"اسم المستخدم موجود مسبقاً.", "weak_password":"كلمة المرور يجب أن تتكون من 8 أحرف على الأقل.",
        "password_mismatch":"كلمتا المرور غير متطابقتين.", "bad_login":"معلومات الدخول غير صحيحة.",
        "demo":"نسخة تجريبية: جميع الأموال افتراضية.", "goal_progress":"تقدم أهداف التوفير",
        "financial_overview":"نظرة مالية عامة", "amount_spent":"المصاريف حسب الصنف",
        "transaction_history":"سجل العمليات", "date":"التاريخ", "kind":"النوع", "details":"التفاصيل",
        "status":"الحالة", "language":"اللغة", "french":"Français", "arabic":"العربية",
        "welcome":"مرحباً", "profile":"الملف الشخصي", "initial_balance":"الرصيد التجريبي الأولي: 1000 درهم",
        "transfer_in":"تحويل مستلم", "transfer_out":"تحويل مرسل", "deposit":"إضافة تجريبية",
        "withdrawal":"سحب تجريبي", "saving":"توفير", "expense_label":"مصروف", "revenue_label":"مدخول",
        "security":"الأمان", "change_password":"تغيير كلمة المرور", "new_password":"كلمة المرور الجديدة",
        "update_password":"تحديث", "password_updated":"تم تحديث كلمة المرور.",
        "empty_goals":"أنشئ هدفاً للبدء في التوفير.", "target_reached":"وصلت إلى هدفك!",
        "total_saved":"مجموع المدخرات", "goal_saved":"تم توفير", "remaining":"المتبقي",
        "all":"الكل", "filter":"تصفية", "search":"بحث", "demo_warning":"تطبيق مدرسي تجريبي — لا توجد تحويلات بنكية حقيقية.",
        "tip":"نصيحة: حدد هدفاً واقعياً وراقب مصاريفك كل أسبوع.",
        "quick_actions":"عمليات سريعة", "monthly":"ملخص الشهر", "net":"صافي العمليات",
        "account_created":"تاريخ إنشاء الحساب", "no_transactions":"لا توجد عمليات تطابق التصفية.",
        "deposit_amount":"المبلغ المراد إضافته", "withdraw_amount":"المبلغ المراد سحبه", "confirm":"تأكيد",
        "transfer_note":"يجب أن يكون المستفيد مسجلاً مسبقاً في DAKHIRTI.",
        "savings_note":"يتم اقتطاع مبلغ التوفير من رصيدك المتاح.",
        "footer":"DAKHIRTI • مشروع تعليمي • الإصدار 1.0"
    }
}

def tr(key):
    return I18N[st.session_state.get("lang", "fr")].get(key, key)

def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

@contextmanager
def db_transaction():
    conn = get_conn()
    try:
        conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE COLLATE NOCASE,
            salt TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            balance REAL NOT NULL DEFAULT 1000,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS transactions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            kind TEXT NOT NULL,
            amount REAL NOT NULL CHECK(amount > 0),
            category TEXT NOT NULL DEFAULT '',
            details TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS goals(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            title TEXT NOT NULL,
            target REAL NOT NULL CHECK(target > 0),
            saved REAL NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );
        """)

def password_hash(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 240000).hex()

def create_user(username, password):
    username = username.strip()
    if len(password) < 8:
        return False, tr("weak_password")
    salt = secrets.token_hex(16)
    digest = password_hash(password, salt)
    try:
        with db_transaction() as conn:
            conn.execute("INSERT INTO users(username,salt,password_hash,balance,created_at) VALUES(?,?,?,?,?)",
                         (username, salt, digest, 1000.0, datetime.now().isoformat(timespec="seconds")))
        return True, tr("register_ok")
    except sqlite3.IntegrityError:
        return False, tr("user_exists")

def authenticate(username, password):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE username=? COLLATE NOCASE", (username.strip(),)).fetchone()
    if not row or password_hash(password, row["salt"]) != row["password_hash"]:
        return None
    return dict(row)

def user_row(user_id):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()

def add_tx(conn, user_id, kind, amount, category="", details=""):
    conn.execute("""INSERT INTO transactions(user_id,kind,amount,category,details,created_at)
                    VALUES(?,?,?,?,?,?)""",
                 (user_id, kind, round(float(amount), 2), category, details,
                  datetime.now().isoformat(timespec="seconds")))

def transfer_money(sender_id, recipient_name, amount, details):
    amount = round(float(amount), 2)
    if amount <= 0:
        return False, tr("error")
    with db_transaction() as conn:
        sender = conn.execute("SELECT * FROM users WHERE id=?", (sender_id,)).fetchone()
        recipient = conn.execute("SELECT * FROM users WHERE username=? COLLATE NOCASE", (recipient_name.strip(),)).fetchone()
        if not recipient:
            return False, tr("recipient_missing")
        if recipient["id"] == sender_id:
            return False, tr("same_user")
        if sender["balance"] < amount:
            return False, tr("insufficient")
        conn.execute("UPDATE users SET balance=balance-? WHERE id=?", (amount, sender_id))
        conn.execute("UPDATE users SET balance=balance+? WHERE id=?", (amount, recipient["id"]))
        add_tx(conn, sender_id, "transfer_out", amount, "Transfert", f"Vers {recipient['username']} — {details}")
        add_tx(conn, recipient["id"], "transfer_in", amount, "Transfert", f"De {sender['username']} — {details}")
    return True, tr("success")

def adjust_balance(user_id, amount, direction):
    amount = round(float(amount), 2)
    if amount <= 0:
        return False, tr("error")
    with db_transaction() as conn:
        row = conn.execute("SELECT balance FROM users WHERE id=?", (user_id,)).fetchone()
        if direction == "withdraw" and row["balance"] < amount:
            return False, tr("insufficient")
        delta = amount if direction == "deposit" else -amount
        conn.execute("UPDATE users SET balance=balance+? WHERE id=?", (delta, user_id))
        add_tx(conn, user_id, direction, amount, "Démo", "Opération de démonstration")
    return True, tr("success")

def create_goal(user_id, title, target):
    target = round(float(target), 2)
    if not title.strip() or target <= 0:
        return False
    with db_transaction() as conn:
        conn.execute("INSERT INTO goals(user_id,title,target,saved,created_at) VALUES(?,?,?,?,?)",
                     (user_id, title.strip(), target, 0, datetime.now().isoformat(timespec="seconds")))
    return True

def contribute_goal(user_id, goal_id, amount):
    amount = round(float(amount), 2)
    if amount <= 0:
        return False, tr("error")
    with db_transaction() as conn:
        user = conn.execute("SELECT balance FROM users WHERE id=?", (user_id,)).fetchone()
        goal = conn.execute("SELECT * FROM goals WHERE id=? AND user_id=?", (goal_id, user_id)).fetchone()
        if not goal:
            return False, tr("error")
        if user["balance"] < amount:
            return False, tr("insufficient")
        conn.execute("UPDATE users SET balance=balance-? WHERE id=?", (amount, user_id))
        conn.execute("UPDATE goals SET saved=saved+? WHERE id=?", (amount, goal_id))
        add_tx(conn, user_id, "saving", amount, "Épargne", f"Objectif : {goal['title']}")
    return True, tr("success")

def add_financial_record(user_id, kind, amount, category, details):
    amount = round(float(amount), 2)
    if amount <= 0:
        return False, tr("error")
    with db_transaction() as conn:
        user = conn.execute("SELECT balance FROM users WHERE id=?", (user_id,)).fetchone()
        if kind == "expense" and user["balance"] < amount:
            return False, tr("insufficient")
        delta = amount if kind == "income" else -amount
        conn.execute("UPDATE users SET balance=balance+? WHERE id=?", (delta, user_id))
        add_tx(conn, user_id, kind, amount, category, details)
    return True, tr("success")

def load_data(user_id):
    with get_conn() as conn:
        user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        tx = pd.read_sql_query("SELECT id,kind,amount,category,details,created_at FROM transactions WHERE user_id=? ORDER BY id DESC",
                               conn, params=(user_id,))
        goals = pd.read_sql_query("SELECT id,title,target,saved,created_at FROM goals WHERE user_id=? ORDER BY id DESC",
                                  conn, params=(user_id,))
    return user, tx, goals

def fmt_money(value):
    return f"{value:,.2f} DH"

def login_view():
    st.markdown("<div class='brand'>DAKHIRTI</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='tagline'>{tr('tagline')}</div>", unsafe_allow_html=True)
    left, center, right = st.columns([1, 1.15, 1])
    with center:
        tab1, tab2 = st.tabs([tr("login"), tr("register")])
        with tab1:
            with st.form("login_form"):
                username = st.text_input(tr("username"))
                password = st.text_input(tr("password"), type="password")
                submitted = st.form_submit_button(tr("login"), use_container_width=True)
            if submitted:
                user = authenticate(username, password)
                if user:
                    st.session_state.user_id = user["id"]
                    st.session_state.username = user["username"]
                    st.rerun()
                else:
                    st.error(tr("bad_login"))
        with tab2:
            with st.form("register_form"):
                new_user = st.text_input(tr("username"), key="reg_user")
                p1 = st.text_input(tr("password"), type="password", key="reg_p1")
                p2 = st.text_input(tr("confirm_password"), type="password")
                submitted = st.form_submit_button(tr("register"), use_container_width=True)
            if submitted:
                if p1 != p2:
                    st.error(tr("password_mismatch"))
                elif not new_user.strip():
                    st.error(tr("error"))
                else:
                    ok, message = create_user(new_user, p1)
                    (st.success if ok else st.error)(message)

def render_dashboard(user, tx, goals):
    st.subheader(f"{tr('welcome')}, {user['username']} 👋")
    st.caption(tr("demo_warning"))
    total_income = tx.loc[tx.kind.isin(["income", "deposit", "transfer_in"]), "amount"].sum() if not tx.empty else 0
    total_expense = tx.loc[tx.kind.isin(["expense", "withdrawal", "transfer_out"]), "amount"].sum() if not tx.empty else 0
    c1,c2,c3 = st.columns(3)
    c1.metric(tr("balance"), fmt_money(user["balance"]))
    c2.metric(tr("income"), fmt_money(total_income))
    c3.metric(tr("expenses"), fmt_money(total_expense))
    st.markdown(f"### {tr('goal_progress')}")
    if goals.empty:
        st.info(tr("empty_goals"))
    else:
        for _, g in goals.iterrows():
            progress = min(float(g["saved"]) / float(g["target"]), 1.0)
            st.write(f"**{g['title']}** — {fmt_money(g['saved'])} / {fmt_money(g['target'])}")
            st.progress(progress)
    st.markdown(f"### {tr('recent')}")
    if tx.empty:
        st.info(tr("no_data"))
    else:
        view = tx.head(6).copy()
        view["amount"] = view["amount"].map(fmt_money)
        view = view.rename(columns={"kind":tr("kind"),"amount":tr("amount"),"category":tr("category"),"details":tr("details"),"created_at":tr("date")})
        st.dataframe(view[[tr("date"),tr("kind"),tr("amount"),tr("category"),tr("details")]], use_container_width=True, hide_index=True)
    st.info(tr("tip"))

def render_transfer(user):
    st.subheader(tr("send_money"))
    st.caption(tr("transfer_note"))
    with st.form("transfer_form"):
        recipient = st.text_input(tr("recipient"))
        amount = st.number_input(tr("amount"), min_value=0.0, step=10.0, format="%.2f")
        details = st.text_input(tr("description"))
        submitted = st.form_submit_button(tr("submit_transfer"), use_container_width=True)
    if submitted:
        ok, message = transfer_money(user["id"], recipient, amount, details)
        (st.success if ok else st.error)(message)
        if ok: st.rerun()

def render_savings(user, goals):
    st.subheader(tr("savings"))
    st.caption(tr("savings_note"))
    with st.expander(tr("create_goal"), expanded=goals.empty):
        with st.form("goal_form"):
            title = st.text_input(tr("goal_name"))
            target = st.number_input(tr("target"), min_value=0.0, step=100.0)
            submitted = st.form_submit_button(tr("create_goal"))
        if submitted:
            if create_goal(user["id"], title, target):
                st.success(tr("success")); st.rerun()
            else: st.error(tr("error"))
    if not goals.empty:
        for _, g in goals.iterrows():
            progress = min(float(g["saved"])/float(g["target"]),1.0)
            with st.container(border=True):
                st.markdown(f"**{g['title']}**")
                st.progress(progress)
                a,b,c = st.columns(3)
                a.metric(tr("goal_saved"),fmt_money(g["saved"]))
                b.metric(tr("target"),fmt_money(g["target"]))
                c.metric(tr("remaining"),fmt_money(max(0,g["target"]-g["saved"])))
                if progress >= 1: st.success(tr("target_reached"))
                with st.form(f"contribute_{int(g['id'])}"):
                    amount=st.number_input(tr("contribution"),min_value=0.0,step=10.0,key=f"amt_{int(g['id'])}")
                    submitted=st.form_submit_button(tr("add_savings"))
                if submitted:
                    ok,msg=contribute_goal(user["id"],int(g["id"]),amount)
                    (st.success if ok else st.error)(msg)
                    if ok: st.rerun()

def render_records(user):
    st.subheader(tr("records"))
    with st.form("record_form"):
        kind_label=st.radio(tr("type"),[tr("expense"),tr("revenue")],horizontal=True)
        kind="expense" if kind_label==tr("expense") else "income"
        amount=st.number_input(tr("amount"),min_value=0.0,step=10.0)
        category=st.selectbox(tr("category"),["Food / أكل","Transport / نقل","Shopping / تسوق","Bills / فواتير","Study / دراسة","Health / صحة","Other / أخرى"])
        details=st.text_input(tr("description"))
        submitted=st.form_submit_button(tr("save_record"),use_container_width=True)
    if submitted:
        ok,msg=add_financial_record(user["id"],kind,amount,category,details)
        (st.success if ok else st.error)(msg)
        if ok: st.rerun()

def render_transactions(tx):
    st.subheader(tr("transaction_history"))
    if tx.empty:
        st.info(tr("no_data")); return
    kinds=sorted(tx["kind"].dropna().unique().tolist())
    chosen=st.multiselect(tr("filter"),kinds,default=kinds)
    filtered=tx[tx.kind.isin(chosen)].copy()
    if filtered.empty:
        st.info(tr("no_transactions")); return
    filtered["amount"]=filtered["amount"].map(fmt_money)
    filtered=filtered.rename(columns={"kind":tr("kind"),"amount":tr("amount"),"category":tr("category"),"details":tr("details"),"created_at":tr("date")})
    st.dataframe(filtered[[tr("date"),tr("kind"),tr("amount"),tr("category"),tr("details")]],use_container_width=True,hide_index=True)

def render_analytics(tx, goals):
    st.subheader(tr("analytics"))
    if tx.empty:
        st.info(tr("no_data")); return
    df=tx.copy()
    df["created_at"]=pd.to_datetime(df["created_at"])
    df["month"]=df["created_at"].dt.strftime("%Y-%m")
    monthly=df[df.kind.isin(["income","expense","deposit","withdrawal","transfer_in","transfer_out"])].copy()
    if not monthly.empty:
        monthly["signed"]=monthly.apply(lambda r: r.amount if r.kind in ["income","deposit","transfer_in"] else -r.amount,axis=1)
        chart=monthly.groupby("month",as_index=False)["signed"].sum()
        st.markdown(f"### {tr('financial_overview')}")
        fig=px.bar(chart,x="month",y="signed",labels={"month":tr("date"),"signed":tr("net")},template="plotly_dark")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig,use_container_width=True)
    expenses=df[df.kind=="expense"]
    if not expenses.empty:
        bycat=expenses.groupby("category",as_index=False)["amount"].sum()
        fig=px.pie(bycat,names="category",values="amount",hole=.55,template="plotly_dark")
        fig.update_layout(title=tr("amount_spent"),paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig,use_container_width=True)
    if not goals.empty:
        st.markdown(f"### {tr('goal_progress')}")
        gd=goals[["title","target","saved"]].melt(id_vars="title",var_name="type",value_name="amount")
        fig=px.bar(gd,x="title",y="amount",color="type",barmode="group",template="plotly_dark")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig,use_container_width=True)

def render_settings(user):
    st.subheader(tr("settings"))
    st.write(f"**{tr('profile')}:** {user['username']}")
    st.write(f"**{tr('account_created')}:** {user['created_at'][:10]}")
    st.markdown(f"### {tr('security')}")
    with st.form("password_form"):
        old=st.text_input(tr("password"),type="password")
        new=st.text_input(tr("new_password"),type="password")
        submitted=st.form_submit_button(tr("update_password"))
    if submitted:
        fresh=authenticate(user["username"],old)
        if not fresh: st.error(tr("bad_login"))
        elif len(new)<8: st.error(tr("weak_password"))
        else:
            salt=secrets.token_hex(16)
            with db_transaction() as conn:
                conn.execute("UPDATE users SET salt=?,password_hash=? WHERE id=?",(salt,password_hash(new,salt),user["id"]))
            st.success(tr("password_updated"))

def main():
    init_db()
    if "lang" not in st.session_state: st.session_state.lang="fr"
    if "user_id" not in st.session_state: st.session_state.user_id=None

    with st.sidebar:
        st.markdown("## 💠 DAKHIRTI")
        st.caption(tr("tagline"))
        lang_choice=st.radio(tr("language"),["Français","العربية"],index=0 if st.session_state.lang=="fr" else 1,horizontal=True)
        st.session_state.lang="fr" if lang_choice=="Français" else "ar"
        st.divider()
        st.caption(tr("demo_warning"))
        if st.session_state.user_id:
            st.write(f"👤 {st.session_state.get('username','')}")
            if st.button(tr("logout"),use_container_width=True):
                st.session_state.user_id=None
                st.session_state.username=None
                st.rerun()

    st.markdown("""
    <style>
    .stApp {background: radial-gradient(circle at 10% 0%, #122c43 0%, #07131f 42%, #050d16 100%); color:#edf5fb;}
    [data-testid="stSidebar"] {background:#081522;}
    .brand {font-size:42px;font-weight:900;letter-spacing:3px;color:#35b9f4;text-align:center;margin-top:18px;}
    .tagline {text-align:center;color:#a9c5d9;margin-bottom:26px;}
    div[data-testid="stMetric"] {background:rgba(16,47,70,.75);border:1px solid rgba(72,171,220,.18);padding:16px;border-radius:14px;}
    .stButton>button, .stFormSubmitButton>button {border-radius:10px;font-weight:700;}
    </style>
    """,unsafe_allow_html=True)

    if not st.session_state.user_id:
        login_view()
        st.markdown(f"<div style='text-align:center;color:#7892a6;margin-top:35px'>{tr('footer')}</div>",unsafe_allow_html=True)
        return

    user,tx,goals=load_data(st.session_state.user_id)
    if user is None:
        st.session_state.user_id=None; st.rerun()
    st.markdown("<div class='brand'>DAKHIRTI</div>",unsafe_allow_html=True)
    st.markdown(f"<div class='tagline'>{tr('tagline')}</div>",unsafe_allow_html=True)

    pages=[tr("dashboard"),tr("transfer"),tr("savings"),tr("records"),tr("transactions"),tr("analytics"),tr("settings")]
    icons=["🏠","💸","🎯","🧾","📜","📊","⚙️"]
    selected=st.radio("Navigation",pages,format_func=lambda x:f"{icons[pages.index(x)]}  {x}",label_visibility="collapsed")
    st.divider()
    if selected==tr("dashboard"): render_dashboard(user,tx,goals)
    elif selected==tr("transfer"): render_transfer(user)
    elif selected==tr("savings"): render_savings(user,goals)
    elif selected==tr("records"): render_records(user)
    elif selected==tr("transactions"): render_transactions(tx)
    elif selected==tr("analytics"): render_analytics(tx,goals)
    elif selected==tr("settings"): render_settings(user)
    st.markdown(f"<div style='text-align:center;color:#7892a6;margin-top:40px'>{tr('footer')}</div>",unsafe_allow_html=True)

if __name__=="__main__":
    main()
