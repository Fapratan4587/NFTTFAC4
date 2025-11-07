import streamlit as st
import pandas as pd
import os
import requests

# ---------------- CONFIG ----------------
st.set_page_config(page_title="ระบบจัดซื้อ Nachi Technology Factory 4", layout="wide")
USERS_FILE = "users.csv"
ORDERS_FILE = "orders.csv"
STOCK_FILE = "orders_stock.xlsx"
STOCK_SHEET = "STOCK DATA"
LOGO_FILE = "logo.png"
LINE_TOKEN = "m1B+eubmf+z3Fyj70Ey1byV2vEOg+kAtUw6pKSWZUpoKDK3ARB4sWuRyUi+i0Fi9e7RwOKwwYqqPjdE3LR/7+GnNBqcV5k4ka/ZMYjb9Tkk90r9iPHMeIMMYnvM67eHFSircOXbp1e8WGSGKCXec6gdB04t89/1O/w1cDnyilFU="  # 🔸 ใส่ Channel access token จาก LINE Developers

# ---------------- STYLE ----------------
st.markdown("""
<style>
:root {
    --main-blue: #0F4C75;
    --accent-blue: #4F81BD;
    --bg: #FFFFFF;
}
body { background-color: var(--bg); }
.stApp { background-color: var(--bg); }
.logo-row { display:flex; align-items:center; gap:12px; }
.company-name { font-size:22px; font-weight:600; color:var(--main-blue); }
.system-title { font-size:14px; color:#666666; }
.stButton>button { background-color: var(--main-blue); color: white; border-radius:8px; padding:6px 12px; }
.card { border:1px solid #e6eef8; padding:12px; border-radius:8px; background:#fbfdff; }
</style>
""", unsafe_allow_html=True)

# ---------------- LINE API ----------------
def send_line_notify(message, user_id=None):
    """ส่งข้อความแจ้งเตือนผ่าน LINE Messaging API"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}"
    }
    payload = {
        "to": user_id,  # ถ้ามี user_id จะส่งเฉพาะคนนั้น
        "messages": [{"type": "text", "text": message}]
    }
    try:
        response = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=payload)
        if response.status_code != 200:
            st.warning(f"⚠️ ส่ง LINE ไม่สำเร็จ: {response.text}")
    except Exception as e:
        st.error(f"ไม่สามารถส่งแจ้งเตือน LINE ได้: {e}")

# ---------------- HELPER FUNCTION ----------------
def load_csv(path, cols):
    if not os.path.exists(path):
        pd.DataFrame(columns=cols).to_csv(path, index=False, encoding="utf-8")
    return pd.read_csv(path, encoding="utf-8")

def save_orders(df):
    df.to_csv(ORDERS_FILE, index=False, encoding="utf-8")

# ---------------- LOAD DATA ----------------
df_users = load_csv(USERS_FILE, ["username", "password", "role", "line_user_id"])
if "line_user_id" not in df_users.columns:
    df_users["line_user_id"] = None

df_orders = load_csv(ORDERS_FILE, ["วันที่","ผู้สั่ง","รหัสสินค้า","ชื่อสินค้า","จำนวน","สถานะ","หมายเหตุ"])

if not os.path.exists(STOCK_FILE):
    st.error(f"❌ ไม่พบไฟล์ {STOCK_FILE}")
    st.stop()

df_products = pd.read_excel(STOCK_FILE, sheet_name=STOCK_SHEET)
df_products = df_products.rename(columns={"DESCRIPTION": "Name", "MODEL": "Model"})
if "price" not in df_products.columns:
    df_products["price"] = 0

# ---------------- SESSION STATE ----------------
if "username" not in st.session_state: st.session_state["username"] = None
if "role" not in st.session_state: st.session_state["role"] = None

# ---------------- HEADER ----------------
col1, col2 = st.columns([1,8])
with col1:
    if os.path.exists(LOGO_FILE):
        st.image(LOGO_FILE, width=250)
with col2:
    st.markdown(f"<div class='logo-row'><div class='company-name'>Nachi Technology (Thailand) (Factory 4)</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='system-title'>ระบบจัดซื้อ Nachi technology Factory 4</div>", unsafe_allow_html=True)
st.divider()

# ---------------- LOGIN ----------------
def check_login(u,p):
    user = df_users[(df_users["username"].astype(str).str.strip()==u.strip()) &
                    (df_users["password"].astype(str).str.strip()==p.strip())]
    if not user.empty:
        return user.iloc[0]["role"]
    return None

if st.session_state["role"] is None:
    st.subheader("เข้าสู่ระบบ")
    username = st.text_input("ชื่อผู้ใช้ (Username)")
    password = st.text_input("รหัสผ่าน (Password)", type="password")
    if st.button("เข้าสู่ระบบ"):
        role = check_login(username,password)
        if role:
            st.session_state["username"] = username
            st.session_state["role"] = role
            st.success(f"เข้าสู่ระบบสำเร็จ ({role})")
            st.rerun()
        else:
            st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

else:
    # --- Sidebar ---
    st.sidebar.markdown(f"**ผู้ใช้:** {st.session_state['username']}  \n**ตำแหน่ง:** {st.session_state['role']}")
    if st.sidebar.button("ออกจากระบบ"):
        st.session_state['username'] = None
        st.session_state['role'] = None
        st.rerun()

    # ---------------- ADMIN ----------------
    if str(st.session_state["role"]).lower() == "admin":
        st.header("🧑‍💼 แดชบอร์ดแอดมิน")
        tabs = st.tabs(["📦 สินค้าจาก Excel", "👤 ผู้ใช้งาน", "🧾 คำสั่งซื้อ"])

        # --- Tab 1: สินค้าจาก Excel ---
        with tabs[0]:
            st.subheader("รายการสินค้า")
            st.dataframe(df_products[["Model","Name"]])

        # --- Tab 2: ผู้ใช้งาน ---
        with tabs[1]:
            st.subheader("จัดการผู้ใช้งาน")
            st.dataframe(df_users)
            with st.expander("เพิ่มผู้ใช้ใหม่"):
                new_user = st.text_input("username", key="nu")
                new_pass = st.text_input("password", type="password", key="np")
                new_role = st.selectbox("role", ["suppervisor","Leader","admin"], key="nr")
                new_line_id = st.text_input("LINE User ID", key="nl")
                if st.button("เพิ่มผู้ใช้", key="adduser"):
                    if new_user and new_pass:
                        if new_user in df_users["username"].values:
                            st.error("ชื่อผู้ใช้นี้มีอยู่แล้ว")
                        else:
                            df_users.loc[len(df_users)] = [new_user,new_pass,new_role,new_line_id]
                            df_users.to_csv(USERS_FILE, index=False, encoding="utf-8")
                            st.success("เพิ่มผู้ใช้เรียบร้อย")
                            st.rerun()

        # --- Tab 3: คำสั่งซื้อ ---
        with tabs[2]:
            st.subheader("คำสั่งซื้อทั้งหมด")
            if df_orders.empty:
                st.info("ยังไม่มีคำสั่งซื้อ")
            else:
                st.dataframe(df_orders)
                for i, row in df_orders.iterrows():
                    if row["สถานะ"] == "รออนุมัติ":
                        c1, c2 = st.columns(2)
                        if c1.button(f"✅ อนุมัติ ({row['ชื่อสินค้า']})"):
                            df_orders.at[i, "สถานะ"] = "✅ อนุมัติแล้ว"
                            save_orders(df_orders)
                            st.success(f"อนุมัติคำสั่งซื้อ {row['ชื่อสินค้า']} แล้ว ✅")

                            # แจ้งเตือน LINE
                            user_info = df_users[df_users["username"] == row["ผู้สั่ง"]]
                            user_id = user_info["line_user_id"].values[0] if not user_info.empty else None
                            if user_id:
                                send_line_notify(f"📢 คำสั่งซื้อของคุณ '{row['ชื่อสินค้า']}' ได้รับการอนุมัติแล้ว ✅", user_id)
                            st.rerun()

                        if c2.button(f"❌ ปฏิเสธ ({row['ชื่อสินค้า']})"):
                            df_orders.at[i, "สถานะ"] = "❌ ปฏิเสธ"
                            save_orders(df_orders)
                            st.warning(f"ปฏิเสธคำสั่งซื้อ {row['ชื่อสินค้า']} แล้ว ❌")
                            st.rerun()

                    elif row["สถานะ"] == "✅ อนุมัติแล้ว":
                        if st.button(f"📦 ได้รับสินค้า ({row['ชื่อสินค้า']})"):
                            df_orders.at[i, "สถานะ"] = "ได้รับสินค้าแล้ว"
                            save_orders(df_orders)
                            st.success(f"อัปเดตคำสั่งซื้อ {row['ชื่อสินค้า']} เป็น 'ได้รับสินค้าแล้ว' ✅")

                            # แจ้งเตือน LINE
                            user_info = df_users[df_users["username"] == row["ผู้สั่ง"]]
                            user_id = user_info["line_user_id"].values[0] if not user_info.empty else None
                            if user_id:
                                send_line_notify(f"📦 สินค้า '{row['ชื่อสินค้า']}' ที่คุณสั่งซื้อได้รับสินค้าแล้ว 🎉", user_id)
                            st.rerun()

    # ---------------- SUPERVISOR / LEADER ----------------
    else:
        st.header("🏭 NACHI FACTORY 4 STORE")
        tab1, tab2 = st.tabs(["🛒 สั่งซื้อสินค้า", "📋 รายการคำสั่งซื้อของฉัน"])

        with tab1:
            st.subheader("รายการสินค้า (สำหรับสั่งซื้อ)")
            search_term = st.text_input("🔍 ค้นหาสินค้า")
            if search_term:
                df_display = df_products[df_products["Name"].str.contains(search_term, case=False, na=False)]
            else:
                df_display = df_products

            st.dataframe(df_display[["Model","Name"]])

            for i, row in df_display.iterrows():
                cols = st.columns([3,1,1])
                cols[0].write(f"**{row['Name']}**")
                qty = cols[1].number_input(f"จำนวน_{i}", min_value=0, step=1, key=f"qty_{i}")
                if cols[0].button(f"สั่งซื้อ_{i}"):
                    if qty > 0:
                        new_order = {
                            "วันที่": pd.Timestamp.now().strftime("%d/%m/%Y %H:%M"),
                            "ผู้สั่ง": st.session_state["username"],
                            "รหัสสินค้า": row["Model"],
                            "ชื่อสินค้า": row["Name"],
                            "จำนวน": qty,
                            "สถานะ": "รออนุมัติ",
                            "หมายเหตุ": ""
                        }
                        df_orders = pd.concat([df_orders, pd.DataFrame([new_order])], ignore_index=True)
                        save_orders(df_orders)
                        st.success(f"ส่งคำสั่งซื้อ {row['Name']} จำนวน {qty} ชิ้นแล้ว ✅")
                        st.rerun()

        with tab2:
            st.subheader("รายการคำสั่งซื้อของฉัน")
            my_orders = df_orders[df_orders["ผู้สั่ง"] == st.session_state["username"]]
            if my_orders.empty:
                st.info("ยังไม่มีคำสั่งซื้อของคุณ")
            else:
                my_orders_display = my_orders.copy()
                my_orders_display.insert(0, "No.", range(1, len(my_orders_display) + 1))
                st.dataframe(my_orders_display)
