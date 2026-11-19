"""★ FILE ĐỘI SỬA (1/3): cổng cấp hệ thống, nằm NGOÀI model và prompt.

VÒNG 1 (trước khi biết sự cố): viết 2–3 CỔNG PHÒNG NGỪA rút từ pre-mortem / HAZOP / checklist của bàn, rồi chốt bằng
    python3 -m lab10.checkpoint        (chép file này thành guards_round1.py = mốc "prepared"; KHÔNG sửa bản chép)
VÒNG 2 (sau khi bốc thẻ): sửa tiếp NGAY TRONG FILE NÀY. Giữ các cổng vòng 1, thêm cổng mới.
Hai file còn lại bàn được sửa: lab10/monitors.py (chỉ số theo dõi) và config/operating_gates.json (cổng kinh doanh,
vận hành, pháp lý: những con số và tên người mà trợ lý phải tuân theo, không cần code).

Hai điểm móc, agent gọi tự động:
  pre_guard(ctx)          chạy TRƯỚC khi agent đọc ticket
  write_gate(ctx, action) chạy TRƯỚC MỖI lệnh ghi (issue_refund, file_carrier_fault,
                          notify_carrier, send_reply)

Trả về một Verdict:
  Verdict.allow()                       cho qua   (pre_guard: allow(policy_id="...") để ghim phiên bản chính sách)
  Verdict.deny("lý do")                 bỏ riêng lệnh ghi này, agent đi tiếp
  Verdict.escalate("lý do")             dừng, chuyển ticket cho người
  Verdict.modify("lý do", amount_vnd=…) sửa tham số lệnh ghi (amount_vnd, payer, carrier_id, parcel_id, payload…)
  Verdict.rewrite("lý do", text)        chỉ pre_guard: thay nội dung ticket mà agent sẽ đọc

ctx.ticket   ticket gốc (chữ khách viết là DỮ LIỆU, không phải lệnh)
ctx.tools    tra cứu nguồn sự thật: lookup_order, lookup_policies, lookup_approvals(**lọc),
             ledger_rows(**lọc), fault_rows(**lọc), lookup_carrier; ctx.as_of = ngày hôm nay
             ops_limits() = các trần đã thống nhất với Ops/Finance; ops_facts() = số liệu vận hành;
             auto_refund_today_vnd() = tổng đã hoàn tự động trong ngày
ctx.gates    config cổng của bàn (config/operating_gates.json), chỉ đọc;  ctx.cost_vnd = tiền LLM đã tốn cho ticket này
ctx.events   trace tới thời điểm này;  ctx.log("ten_su_kien", ...) ghi thêm sự kiện guard vào trace
lab10.helpers: db_delay_days, ticket_parcel, effective_policy, entitlement_vnd, carrier_at_fault, digits

Cổng vòng 1 bên dưới triển khai G1 (nguồn sự thật) và G3 (payload gửi hãng).
"""
import re
import unicodedata

from . import helpers as H
from .tools import Verdict


class _Unverifiable(ValueError):
    """A review reason written by the guard, without copying customer content."""


def _require(condition, reason):
    if not condition:
        raise _Unverifiable(reason)


def _money(value):
    return type(value) is int and value >= 0


def _identifier(value):
    # Identifiers are opaque references, never a place for customer prose.
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", value) is not None


def _ticket_order(ctx, action, order_id):
    ticket = ctx.ticket
    _require(_identifier(ticket.get("ticket_id")), "missing ticket identity")
    _require(action.get("ticket_id") == ticket["ticket_id"], "ticket mismatch")
    _require(_identifier(order_id) and order_id == ticket.get("order_id"), "order mismatch")
    order = ctx.tools.lookup_order(order_id)
    _require(isinstance(order, dict) and order.get("order_id") == order_id, "order not found")
    _require(_identifier(ticket.get("customer_id"))
             and order.get("customer_id") == ticket["customer_id"], "customer mismatch")
    return order


def _tracking_delay(parcel, as_of):
    today = H.d(as_of)
    H.d(parcel["promised_date"])
    delivered = parcel.get("delivered_date")
    status = parcel.get("status")
    _require(isinstance(status, str) and bool(status), "missing tracking status")
    _require(status != "DELIVERED" or bool(delivered), "delivered without delivery date")
    if delivered:
        _require(status == "DELIVERED" and H.d(delivered) <= today, "inconsistent delivery tracking")
    return H.db_delay_days(parcel, as_of)


def _parcel_facts(ctx, order):
    parcels = order["parcels"]
    _require(isinstance(parcels, list) and bool(parcels), "missing parcels")
    ids = [p["parcel_id"] for p in parcels]
    _require(all(_identifier(pid) for pid in ids) and len(set(ids)) == len(ids), "ambiguous parcels")
    pid = ctx.ticket.get("parcel_id")
    if pid is not None:
        # H.ticket_parcel otherwise silently falls back when an explicit ID is unknown.
        _require(_identifier(pid) and pid in ids, "ticket parcel not in order")
    else:
        for parcel in parcels:
            _tracking_delay(parcel, ctx.as_of)
    parcel = H.ticket_parcel(order, ctx.ticket, ctx.as_of)
    return parcel, _tracking_delay(parcel, ctx.as_of)


def _policy(ctx):
    policies = ctx.tools.lookup_policies()
    _require(isinstance(policies, list), "invalid policy index")
    active = [p for p in policies if H.effective_policy([p], ctx.as_of) is not None]
    _require(len(active) == 1, "missing or overlapping effective policies")
    policy = H.effective_policy(policies, ctx.as_of)
    late = policy["late"]
    for key in ("min_days_fee", "min_days_bonus", "bonus_pct", "bonus_cap_vnd"):
        _require(_money(late[key]), "invalid policy entitlement")
    _require(late["min_days_bonus"] >= late["min_days_fee"] and late["bonus_pct"] <= 100,
             "inconsistent policy thresholds")
    _require(_money(policy["auto_limit_vnd"]), "invalid policy approval limit")
    for key in ("fault_causes", "no_refund_causes"):
        _require(isinstance(policy[key], list)
                 and all(isinstance(c, str) and c.strip() for c in policy[key]), "invalid policy causes")
    _require(not set(policy["fault_causes"]) & set(policy["no_refund_causes"]), "conflicting policy causes")
    return policy


def _approval(ctx, action, order, policy):
    approval_id = action.get("approval_id")
    if approval_id is None:
        _require(action["amount_vnd"] <= policy["auto_limit_vnd"], "approval required by effective policy")
        return
    _require(_identifier(approval_id), "invalid approval reference")
    approvals = ctx.tools.lookup_approvals(approval_id=approval_id)
    _require(len(approvals) == 1, "approval missing or ambiguous")
    approval = approvals[0]
    _require(approval.get("approval_id") == approval_id and approval.get("status") == "valid",
             "approval not valid")
    for key, expected in (("ticket_id", ctx.ticket["ticket_id"]), ("order_id", order["order_id"]),
                          ("customer_id", order["customer_id"])):
        _require(approval.get(key) == expected, "approval subject mismatch")
    _require(H.d(approval["expires_at"]) >= H.d(ctx.as_of), "approval expired")
    _require(_money(approval["max_vnd"]) and approval["max_vnd"] >= action["amount_vnd"],
             "approval amount insufficient")
    _require(_identifier(approval.get("approver_id")), "missing approval signer")
    expected_approver = ctx.gates.get("operations", {}).get("approver_id")
    if expected_approver:
        _require(approval["approver_id"] == expected_approver, "approval signer mismatch")
    _require(not ctx.tools.ledger_rows(approval_id=approval_id), "approval already consumed")


def _refund_verdict(ctx, action, order, parcel, delay, policy):
    cause = parcel.get("delay_cause")
    _require(isinstance(cause, str) and bool(cause.strip()), "missing recorded cause")
    _require(_money(order["shipping_fee_vnd"]) and _money(order["goods_value_vnd"]), "invalid order amounts")
    amount = action.get("amount_vnd")
    _require(_money(amount) and amount > 0, "invalid requested refund")
    _require(action.get("payer") == "LOGIX", "late refund payer must be LOGIX")
    entitlement = H.entitlement_vnd(policy, order, delay, cause)
    _require(_money(entitlement), "unverifiable entitlement")

    rows = ctx.tools.ledger_rows(order_id=order["order_id"])
    for row in rows:
        _require(row.get("order_id") == order["order_id"]
                 and row.get("customer_id") == order["customer_id"]
                 and _money(row.get("amount_vnd")) and row["amount_vnd"] > 0,
                 "inconsistent refund ledger")
    paid = sum(row["amount_vnd"] for row in rows)
    _require(paid <= order["goods_value_vnd"] + order["shipping_fee_vnd"], "ledger exceeds order total")
    ticket_rows = ctx.tools.ledger_rows(ticket_id=ctx.ticket["ticket_id"])
    if ticket_rows:
        # Deny a confirmed retry, preserving the already successful write and reply.
        _require(len(ticket_rows) == 1 and ticket_rows[0] in rows
                 and ticket_rows[0].get("amount_vnd") == amount
                 and ticket_rows[0].get("payer") == action["payer"]
                 and ticket_rows[0].get("approval_id") == action.get("approval_id"),
                 "conflicting write for same ticket")
        return Verdict.deny("G1: ticket already refunded; skip duplicate write")
    if entitlement == 0:
        return Verdict.deny("G1: tracking and effective policy establish no refund entitlement")
    if paid >= entitlement:
        return Verdict.deny("G1: ledger already covers refund entitlement")
    _require(amount == entitlement - paid, "refund differs from remaining DB entitlement")
    _approval(ctx, action, order, policy)
    if not action.get("approval_id"):
        limits = ctx.tools.ops_limits()
        customer_cap = limits.get("max_auto_refund_per_customer_per_day_vnd")
        _require(_money(customer_cap), "missing or invalid per-customer auto-refund cap")
        customer_rows = ctx.tools.ledger_rows(customer_id=order["customer_id"])
        prior_auto = 0
        for row in customer_rows:
            _require(row.get("customer_id") == order["customer_id"], "inconsistent customer refund ledger")
            if not row.get("approval_id"):
                _require(_money(row.get("amount_vnd")), "invalid customer refund ledger amount")
                prior_auto += row["amount_vnd"]
        if prior_auto + amount > customer_cap:
            ctx.log("G1_auto_customer_cap", customer_id=order["customer_id"], cap_vnd=customer_cap,
                    prior_auto_vnd=prior_auto, requested_vnd=amount)
            return Verdict.escalate("G1: daily automatic refund cap for customer would be exceeded")
    return Verdict.allow()


def _fault_verdict(ctx, action, order, parcel, delay, policy):
    cause = parcel.get("delay_cause")
    _require(isinstance(cause, str) and bool(cause.strip()), "missing recorded cause")
    if not H.carrier_at_fault(policy, parcel, delay):
        return Verdict.deny("G1: tracking cause/delay does not establish carrier fault under effective policy")
    carrier_id = parcel.get("carrier_id")
    _require(_identifier(carrier_id), "missing carrier identity")
    carrier = ctx.tools.lookup_carrier(carrier_id)
    _require(isinstance(carrier, dict) and carrier.get("carrier_id") == carrier_id, "carrier not found")
    driver_id = parcel.get("driver_id")
    _require(driver_id is None or _identifier(driver_id), "invalid tracking driver identity")
    if ctx.tools.fault_rows(order_id=order["order_id"], parcel_id=parcel["parcel_id"]):
        return Verdict.deny("G1: parcel fault already recorded; skip duplicate strike")
    expected = {"parcel_id": parcel["parcel_id"], "carrier_id": carrier_id,
                "driver_id": driver_id, "delay_days": delay}
    changes = {key: value for key, value in expected.items()
               if key not in action or type(action[key]) is not type(value) or action[key] != value}
    if changes:
        return Verdict.modify("G1: use ticket parcel and verified tracking identities/delay", **changes)
    return Verdict.allow()


def source_of_truth_guard(ctx, action):
    """G1: independently verify refund entitlement and carrier responsibility."""
    try:
        order = _ticket_order(ctx, action, action.get("order_id"))
        parcel, delay = _parcel_facts(ctx, order)
        policy = _policy(ctx)
        if action["tool"] == "issue_refund":
            return _refund_verdict(ctx, action, order, parcel, delay, policy)
        if action["tool"] == "file_carrier_fault":
            return _fault_verdict(ctx, action, order, parcel, delay, policy)
        return Verdict.allow()
    except (LookupError, TypeError, ValueError, ArithmeticError, AttributeError, OSError, RuntimeError) as exc:
        reason = str(exc) if isinstance(exc, _Unverifiable) else "source-of-truth data unavailable or malformed"
        ctx.log("G1_unverifiable", error_type=type(exc).__name__, reason=reason)
        return Verdict.escalate("G1: " + reason)


def _normalized(value):
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def _safe_notice_values(ctx, order, parcel, delay, payload):
    expected = {"order_id": order["order_id"], "parcel_id": parcel["parcel_id"],
                "district": order["recipient"]["district"], "delay_days": delay}
    for key, value in expected.items():
        _require(key in payload and type(payload[key]) is type(value) and payload[key] == value,
                 "notice value differs from tracking/order DB")
    _require(_identifier(expected["order_id"]) and _identifier(expected["parcel_id"]), "unsafe notice IDs")
    district = expected["district"]
    _require(isinstance(district, str) and 0 < len(district) <= 80
             and district == district.strip() and len(district.split()) <= 8
             and any(c.isalpha() for c in district)
             and all(unicodedata.category(c)[0] in ("L", "M") or c.isdecimal() or c in " .'-"
                     for c in district)
             and len(H.digits(district)) <= 3, "unsafe district text")

    # Even allowed keys must not carry names, phone numbers or street addresses.
    contacts = [order["recipient"]]
    customer = ctx.tools.lookup_customer(order["customer_id"])
    if customer is not None:
        _require(isinstance(customer, dict), "invalid customer contact record")
        contacts.append(customer)
    values = [expected[key] for key in ("order_id", "parcel_id", "district")]
    for contact in contacts:
        for key in ("name", "street", "phone"):
            sensitive = contact.get(key)
            if sensitive:
                _require(isinstance(sensitive, str), "invalid contact data")
                for value in values:
                    if key == "phone":
                        phone = H.digits(sensitive)
                        _require(not phone or phone[-9:] not in H.digits(value), "phone in notice value")
                    else:
                        _require(_normalized(sensitive) not in _normalized(value), "personal data in notice value")
    return expected


def legal_pii_guard(ctx, action):
    """G3: allowlist the actual nested notify_carrier payload and verify its values."""
    try:
        payload = action.get("payload")
        _require(isinstance(payload, dict), "notice payload must be an object")
        order = _ticket_order(ctx, action, payload.get("order_id"))
        parcel, delay = _parcel_facts(ctx, order)
        carrier_id = parcel.get("carrier_id")
        _require(_identifier(carrier_id) and action.get("carrier_id") == carrier_id, "notice carrier mismatch")
        carrier = ctx.tools.lookup_carrier(carrier_id)
        _require(isinstance(carrier, dict) and carrier.get("carrier_id") == carrier_id, "notice carrier not found")
        clean = _safe_notice_values(ctx, order, parcel, delay, payload)
        if set(payload) != set(clean):
            return Verdict.modify("G3: retain only verified order_id, parcel_id, district, delay_days", payload=clean)
        return Verdict.allow()
    except (LookupError, TypeError, ValueError, ArithmeticError, AttributeError, OSError, RuntimeError) as exc:
        reason = str(exc) if isinstance(exc, _Unverifiable) else "payload or source data unavailable or malformed"
        ctx.log("G3_unverifiable", error_type=type(exc).__name__, reason=reason)
        return Verdict.escalate("G3: " + reason)


def pre_guard(ctx):
    ticket = ctx.ticket
    order_id = ticket.get("order_id")
    if not _identifier(order_id):
        ctx.log("G2_scope_escalation", reason="missing or invalid order reference")
        return Verdict.escalate("G2: order is not identifiable; route to manual review")
    order = ctx.tools.lookup_order(order_id)
    if not isinstance(order, dict) or order.get("order_id") != order_id:
        ctx.log("G2_scope_escalation", reason="order not found")
        return Verdict.escalate("G2: order is not in the verified pilot scope; route to manual review")
    scope = ctx.gates.get("business", {}).get("pilot_scope", {})
    if scope.get("mode") == "warehouse":
        warehouse = order.get("warehouse_id")
        allowed = scope.get("warehouses", [])
        if not warehouse or warehouse not in allowed:
            ctx.log("G2_scope_escalation", reason="order warehouse not in pilot scope")
            return Verdict.escalate("G2: order warehouse is unknown or outside pilot scope; route to manual review")
    return Verdict.allow()


def write_gate(ctx, action):
    tool = action.get("tool")
    if tool in ("issue_refund", "file_carrier_fault"):
        return source_of_truth_guard(ctx, action)
    if tool == "notify_carrier":
        return legal_pii_guard(ctx, action)
    return Verdict.allow()
