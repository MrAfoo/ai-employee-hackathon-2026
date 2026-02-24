"""
Odoo MCP Server – integrates with Odoo Community via JSON-RPC.

Exposes REST endpoints for Claude to query/create accounting records.

Endpoints:
  GET  /health
  GET  /invoices          – list invoices
  GET  /partners          – list customers/vendors
  POST /invoice/create    – create a draft invoice
  GET  /journal_entries   – list journal entries
  POST /report/profit_loss – generate P&L summary
"""
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [OdooMCP] %(levelname)s %(message)s")
log = logging.getLogger(__name__)

app = FastAPI(title="Odoo MCP Server", version="1.0.0")


class OdooClient:
    """JSON-RPC client for Odoo Community Edition."""

    def __init__(self):
        self.url = os.getenv("ODOO_URL", "http://localhost:8069")
        self.db = os.getenv("ODOO_DB", "odoo")
        self.username = os.getenv("ODOO_USERNAME", "admin")
        self.password = os.getenv("ODOO_PASSWORD", "admin")
        self._uid: Optional[int] = None

    def _jsonrpc(self, endpoint: str, method: str, params: dict) -> Any:
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": params,
            "id": 1,
        }
        resp = requests.post(f"{self.url}{endpoint}", json=payload, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        if "error" in result:
            raise RuntimeError(f"Odoo error: {result['error']}")
        return result.get("result")

    def authenticate(self) -> int:
        if self._uid:
            return self._uid
        self._uid = self._jsonrpc(
            "/web/dataset/call_kw",
            "call",
            {
                "service": "common",
                "method": "authenticate",
                "args": [self.db, self.username, self.password, {}],
            },
        )
        if not self._uid:
            raise RuntimeError("Odoo authentication failed.")
        log.info("Authenticated with Odoo as UID %d", self._uid)
        return self._uid

    def call(self, model: str, method: str, args: list, kwargs: dict = None) -> Any:
        uid = self.authenticate()
        return self._jsonrpc(
            "/web/dataset/call_kw",
            "call",
            {
                "service": "object",
                "method": "execute_kw",
                "args": [
                    self.db,
                    uid,
                    self.password,
                    model,
                    method,
                    args,
                    kwargs or {},
                ],
            },
        )

    def search_read(self, model: str, domain: list, fields: list, limit: int = 50) -> list:
        return self.call(model, "search_read", [domain], {"fields": fields, "limit": limit})


odoo = OdooClient()


class InvoiceCreate(BaseModel):
    partner_name: str
    amount: float
    currency: str = "USD"
    description: str = "Invoice"
    move_type: str = "out_invoice"  # out_invoice=customer, in_invoice=vendor


@app.get("/health")
def health():
    try:
        odoo.authenticate()
        return {"status": "ok", "odoo_url": odoo.url, "db": odoo.db}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


@app.get("/invoices")
def list_invoices(limit: int = 20, state: str = "posted"):
    try:
        domain = [["move_type", "in", ["out_invoice", "in_invoice"]]]
        if state != "all":
            domain.append(["state", "=", state])
        records = odoo.search_read(
            "account.move",
            domain,
            ["name", "partner_id", "invoice_date", "amount_total", "state", "move_type"],
            limit=limit,
        )
        return {"invoices": records, "count": len(records)}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/partners")
def list_partners(limit: int = 50, type: str = "customer"):
    try:
        domain = []
        if type == "customer":
            domain = [["customer_rank", ">", 0]]
        elif type == "vendor":
            domain = [["supplier_rank", ">", 0]]
        records = odoo.search_read(
            "res.partner",
            domain,
            ["name", "email", "phone", "customer_rank", "supplier_rank"],
            limit=limit,
        )
        return {"partners": records, "count": len(records)}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.post("/invoice/create")
def create_invoice(req: InvoiceCreate):
    try:
        # Find or create partner
        partners = odoo.search_read("res.partner", [["name", "ilike", req.partner_name]], ["id", "name"], limit=1)
        if partners:
            partner_id = partners[0]["id"]
        else:
            partner_id = odoo.call("res.partner", "create", [{"name": req.partner_name}])

        # Create invoice
        invoice_vals = {
            "move_type": req.move_type,
            "partner_id": partner_id,
            "invoice_date": datetime.now().strftime("%Y-%m-%d"),
            "invoice_line_ids": [(0, 0, {
                "name": req.description,
                "quantity": 1.0,
                "price_unit": req.amount,
            })],
        }
        invoice_id = odoo.call("account.move", "create", [invoice_vals])
        return {"invoice_id": invoice_id, "partner_id": partner_id, "status": "draft"}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/journal_entries")
def list_journal_entries(limit: int = 20):
    try:
        records = odoo.search_read(
            "account.move",
            [["move_type", "=", "entry"]],
            ["name", "date", "journal_id", "amount_total", "state"],
            limit=limit,
        )
        return {"journal_entries": records, "count": len(records)}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.get("/report/profit_loss")
def profit_loss_summary():
    """Return a simple P&L summary from account balances."""
    try:
        # Revenue accounts (type income)
        revenue = odoo.search_read(
            "account.account",
            [["account_type", "=", "income"]],
            ["name", "code", "current_balance"],
            limit=100,
        )
        # Expense accounts
        expenses = odoo.search_read(
            "account.account",
            [["account_type", "=", "expense"]],
            ["name", "code", "current_balance"],
            limit=100,
        )
        total_revenue = sum(a.get("current_balance", 0) for a in revenue)
        total_expenses = sum(a.get("current_balance", 0) for a in expenses)
        return {
            "generated": datetime.now().isoformat(),
            "total_revenue": total_revenue,
            "total_expenses": total_expenses,
            "net_profit": total_revenue - total_expenses,
            "revenue_accounts": revenue,
            "expense_accounts": expenses,
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


if __name__ == "__main__":
    host = os.getenv("ODOO_MCP_HOST", "0.0.0.0")
    port = int(os.getenv("ODOO_MCP_PORT", "8004"))
    uvicorn.run(app, host=host, port=port)
