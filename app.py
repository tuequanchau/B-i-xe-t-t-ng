import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

# ==========================================
# 1. CẤU HÌNH TRANG STREAMLIT
# ==========================================
st.set_page_config(
    page_title="Hệ thống Tối ưu Bãi đỗ xe Tự động", layout="wide"
)

st.title("🚗 Hệ thống Tối ưu Bãi đỗ xe Tự động")

# ==========================================
# 2. KHỞI TẠO BÃI ĐỖ XE 60 Ô (6x10)
# ==========================================
ROWS = 6
COLS = 10

if "parking_lots" not in st.session_state:
  np.random.seed(42)
  slots = []

  for y in range(1, ROWS + 1):
    for x in range(1, COLS + 1):
      slot_id = f"X{x}Y{y}"

      k_j = 0  # Trạm sạc
      pr_j = 0  # Ô ưu tiên

      # 1. 12 Ô trạm sạc thường sát Cổng vào (Cột 1, 2)
      if x in [1, 2]:
        k_j = 1

      # 2. 4 Ô ƯU TIÊN THƯỜNG (Cột 10 tại Hàng 2, 3, 4, 5)
      if x == 10 and y in [2, 3, 4, 5]:
        pr_j = 1

      # 3. 2 Ô ƯU TIÊN CÓ TRẠM SẠC (Cột 9 tại Hàng 3, 4)
      if x == 9 and y in [3, 4]:
        pr_j = 1
        k_j = 1

      # Giả lập 25% ô đỗ sẵn
      occupied = False
      if pr_j == 0 and np.random.rand() < 0.25:
        occupied = True

      slots.append({
          "id": slot_id,
          "x": x,
          "y": y,
          "k_j": k_j,
          "pr_j": pr_j,
          "occupied": occupied,
      })

  st.session_state.parking_lots = slots

# ==========================================
# 3. GIAO DIỆN NHẬP DỮ LIỆU XE
# ==========================================
st.sidebar.header("📋 Khai báo Xe vào Cổng")

p_i = 1 if st.sidebar.checkbox("♿ Xe Ưu tiên", value=False) else 0

engine_type = st.sidebar.radio("Loại xe", ["Xe xăng / Không sạc", "Xe điện"])
e_i = 1 if "Xe điện" in engine_type else 0

c_i = 0
if e_i == 1:
  c_i = 1 if st.sidebar.checkbox("Cần sạc điện", value=True) else 0

# ==========================================
# 4. THUẬT TOÁN ĐIỀU PHỐI TỐI ƯU CẬP NHẬT
# ==========================================
parking_lots = st.session_state.parking_lots
available_slots = [s for s in parking_lots if not s["occupied"]]
avail_dict = {s["id"]: s for s in available_slots}

best_slot = None
is_priority_fallback = False

if p_i == 1:
  if c_i == 1:
    # 1. Xe Ưu tiên Điện có sạc: Ưu tiên đỗ ô Sạc Ưu tiên (X9Y3 -> X9Y4)
    p_charge_order = ["X9Y3", "X9Y4"]
    for sid in p_charge_order:
      if sid in avail_dict:
        best_slot = avail_dict[sid]
        break

    # 2. Hết ô Sạc Ưu tiên -> Đỗ sang Ô TRẠM SẠC THƯỜNG theo thứ tự X (10->1), Y (3,4,2,5,1,6)
    if not best_slot:
      priority_charge_y_order = [3, 4, 2, 5, 1, 6]
      for x in range(10, 0, -1):
        for y in priority_charge_y_order:
          target_id = f"X{x}Y{y}"
          if target_id in avail_dict:
            if avail_dict[target_id]["k_j"] == 1 and avail_dict[target_id]["pr_j"] == 0:
              best_slot = avail_dict[target_id]
              break
        if best_slot:
          break

  else:
    # Xe Ưu tiên Xăng: Ưu tiên theo thứ tự X10Y3 -> X10Y4 -> X10Y2 -> X10Y5
    p_gas_order = ["X10Y3", "X10Y4", "X10Y2", "X10Y5"]
    for sid in p_gas_order:
      if sid in avail_dict:
        best_slot = avail_dict[sid]
        break

  if not best_slot:
    is_priority_fallback = True

# Trường hợp Xe Ưu tiên HẾT TOÀN BỘ Ô CHUYÊN DỤNG & Ô SẠC -> Đỗ ô thường sát Lối ra:
# X giảm từ 10 -> 1, Y theo thứ tự: 3, 4, 2, 5, 1, 6
if is_priority_fallback and not best_slot:
  priority_fallback_y_order = [3, 4, 2, 5, 1, 6]

  for x in range(10, 0, -1):
    for y in priority_fallback_y_order:
      target_id = f"X{x}Y{y}"
      if target_id in avail_dict:
        if avail_dict[target_id]["pr_j"] == 0:
          best_slot = avail_dict[target_id]
          break
    if best_slot:
      break

# Luồng xử lý cho Xe Thường (p_i = 0)
if p_i == 0 and not best_slot:
  if c_i == 1:
    # Xe điện thường cần sạc: X từ 2 -> 1, Y theo thứ tự: 1, 6, 2, 5, 3, 4
    normal_x_charge_order = [2, 1]
    normal_y_charge_order = [1, 6, 2, 5, 3, 4]

    for x in normal_x_charge_order:
      for y in normal_y_charge_order:
        target_id = f"X{x}Y{y}"
        if target_id in avail_dict:
          if avail_dict[target_id]["k_j"] == 1 and avail_dict[target_id]["pr_j"] == 0:
            best_slot = avail_dict[target_id]
            break
      if best_slot:
        break

  if not best_slot:
    # Xe Xăng Thường: X giảm từ 10 -> 1, Y theo thứ tự: 1, 6, 2, 5, 3, 4
    normal_y_priority_order = [1, 6, 2, 5, 3, 4]

    for x in range(10, 0, -1):
      for y in normal_y_priority_order:
        target_id = f"X{x}Y{y}"
        if target_id in avail_dict:
          if avail_dict[target_id]["pr_j"] == 0:
            best_slot = avail_dict[target_id]
            break
      if best_slot:
        break

# ==========================================
# 5. CHẾ ĐỘ THAO TÁC, TEST PHẠT & ĐỔI TRẠNG THÁI Ô
# ==========================================
st.sidebar.markdown("---")
st.sidebar.subheader("🕹️ Chế độ Đỗ xe")

mode = st.sidebar.radio(
    "Chế độ:", ["Chỉ dẫn Hệ thống", "Tự chọn ô đỗ"]
)

if mode == "Chỉ dẫn Hệ thống":
  if st.sidebar.button(
      "🚗 ĐỖ XE THEO GỢI Ý", type="primary", use_container_width=True
  ):
    if best_slot:
      for s in st.session_state.parking_lots:
        if s["id"] == best_slot["id"]:
          s["occupied"] = True
          break
      st.rerun()
else:
  available_ids = [s["id"] for s in available_slots]
  if available_ids:
    selected_id = st.sidebar.selectbox("Chọn ô cố tình đỗ:", available_ids)
    target_s = next(s for s in parking_lots if s["id"] == selected_id)

    is_penalty = target_s["k_j"] == 1 and c_i == 0

    if is_penalty:
      st.sidebar.error("🚨 LỖI PHẠT (μ_ij = 1): Xe không sạc chiếm ô sạc!")

    if st.sidebar.button(
        "⚠️ ÉP ĐỖ VÀO Ô ĐÃ CHỌN", type="primary", use_container_width=True
    ):
      for s in st.session_state.parking_lots:
        if s["id"] == selected_id:
          s["occupied"] = True
          break
      st.rerun()

# CÔNG CỤ THAY ĐỔI TRẠNG THÁI Ô ĐỖ
st.sidebar.markdown("---")
with st.sidebar.expander("🔄 Thay đổi Trạng thái Ô đỗ (Đỗ/Trống)"):
  slot_to_toggle = st.selectbox(
      "Chọn ô cần đổi:", [s["id"] for s in parking_lots]
  )
  if st.button("Đổi Trạng Thái Ô Này"):
    for s in st.session_state.parking_lots:
      if s["id"] == slot_to_toggle:
        s["occupied"] = not s["occupied"]
        break
    st.rerun()

if st.sidebar.button("🔄 Đặt lại Bãi đỗ (Reset)", use_container_width=True):
  del st.session_state.parking_lots
  st.rerun()

# ==========================================
# 6. HIỂN THỊ SƠ ĐỒ MẶT BẰNG & CHỈ DẪN
# ==========================================
c1, c2, c3 = st.columns(3)
total_s = len(st.session_state.parking_lots)
occ_s = sum(1 for s in st.session_state.parking_lots if s["occupied"])
c1.metric("Tổng quy mô", f"{total_s} ô")
c2.metric("Ô trống", f"{total_s - occ_s} ô")
c3.metric("Xe đã đỗ", f"{occ_s} xe")

st.markdown("---")

col_map, col_info = st.columns([2.5, 1])

with col_map:
  st.subheader("🗺️ Sơ đồ Mặt bằng Bãi đỗ xe")

  fig, ax = plt.subplots(figsize=(10, 5.5))

  for s in st.session_state.parking_lots:
    x_pos = s["x"]
    y_pos = s["y"] if s["y"] <= 3 else s["y"] + 1.2

    if s["occupied"]:
      color = "#ef9a9a"  # Đỏ
      lbl = "ĐÃ ĐỖ"
    elif best_slot and s["id"] == best_slot["id"]:
      color = "#81c784"  # Xanh lá
      lbl = "CHỌN"
    elif s["pr_j"] == 1 and s["k_j"] == 1:
      color = "#ab47bc"  # Tím đậm: Ô Ưu tiên Có Trạm Sạc (X9Y3, X9Y4)
      lbl = "⚡♿"
    elif s["pr_j"] == 1:
      color = "#e1bee7"  # Tím nhạt: Ô Ưu tiên Thường (X10Y2..5)
      lbl = "♿"
    elif s["k_j"] == 1:
      color = "#fff59d"  # Vàng: Ô Trạm sạc Thường
      lbl = "⚡"
    else:
      color = "#e3f2fd"  # Xanh nhạt: Ô Thường
      lbl = "TRỐNG"

    rect = plt.Rectangle(
        (x_pos - 0.4, y_pos - 0.4),
        0.8,
        0.8,
        facecolor=color,
        edgecolor="#37474f",
        lw=1.2,
    )
    ax.add_patch(rect)

    text_color = "white" if (s["pr_j"] == 1 and s["k_j"] == 1 and not s["occupied"]) else "black"

    ax.text(
        x_pos,
        y_pos + 0.1,
        s["id"],
        ha="center",
        va="center",
        fontsize=6.0,
        fontweight="bold",
        color=text_color,
    )
    ax.text(
        x_pos,
        y_pos - 0.15,
        lbl,
        ha="center",
        va="center",
        fontsize=6,
        color=text_color,
    )

  # LÀN ĐƯỜNG CHÍNH GIỮA
  ax.add_patch(
      plt.Rectangle(
          (0.5, 3.6), 10.0, 1.0, facecolor="#eceff1", edgecolor="#b0bec5", ls="--"
      )
  )
  ax.text(
      5.5,
      4.1,
      "🛣️ LÀN ĐƯỜNG CHÍNH (MAIN DRIVEWAY)",
      ha="center",
      va="center",
      fontsize=8,
      fontweight="bold",
      color="#455a64",
  )

  # Cổng vào & Lối ra
  ax.text(
      0.8,
      4.1,
      "🚪 CỔNG VÀO",
      ha="center",
      va="center",
      fontsize=7.5,
      fontweight="bold",
      bbox=dict(boxstyle="round,pad=0.3", facecolor="#ffe0b2", edgecolor="orange"),
  )
  ax.text(
      10.2,
      4.1,
      "🚶 LỐI RA",
      ha="center",
      va="center",
      fontsize=7.5,
      fontweight="bold",
      bbox=dict(boxstyle="round,pad=0.3", facecolor="#c8e6c9", edgecolor="green"),
  )

  # Mũi tên di chuyển
  if best_slot:
    bx = best_slot["x"]
    by = best_slot["y"] if best_slot["y"] <= 3 else best_slot["y"] + 1.2
    ax.annotate(
        "",
        xy=(bx, 4.1),
        xytext=(1.0, 4.1),
        arrowprops=dict(
            arrowstyle="->", color="#1b5e20", lw=2.5, mutation_scale=15
        ),
    )
    ax.annotate(
        "",
        xy=(bx, by),
        xytext=(bx, 4.1),
        arrowprops=dict(
            arrowstyle="->", color="#1b5e20", lw=2.5, mutation_scale=15
        ),
    )

  ax.set_xlim(0.0, 11.0)
  ax.set_ylim(0.3, 8.0)
  ax.set_aspect("equal")
  ax.axis("off")

  st.pyplot(fig)

  st.markdown(
      "**Chú thích màu:** 🟩 Ô chọn đỗ | 🟨 Ô sạc thường (⚡) | 🪻 Ô Ưu tiên"
      " sạc (⚡♿) | 🟪 Ô Ưu tiên thường (♿) | 🟦 Ô thường | 🟥 Đã đỗ"
  )

with col_info:
  st.subheader("📌 Chỉ dẫn Hệ thống")
  if best_slot:
    st.success(f"🎯 **Ô CHỌN GÁN: {best_slot['id']}**")
  else:
    st.error("❌ Không có ô đỗ phù hợp!")

  st.markdown("---")
  st.subheader("ℹ️ Thông tin Khai báo Xe")
  st.write(
      f"- **Động cơ:** {'Xe điện ⚡' if e_i==1 else 'Xe xăng 🚗'}"
  )

  if e_i == 1:
    st.write(
        f"- **Nhu cầu sạc:** {'Có nhu cầu sạc' if c_i==1 else 'Không sạc'}"
    )

  if p_i == 1:
    st.info("♿ **Đối tượng Ưu tiên**")