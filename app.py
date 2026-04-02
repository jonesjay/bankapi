# ...existing code...
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict
from uuid import uuid4
from threading import Lock
import uvicorn

app = FastAPI(title="BankAPI - Sample Start")

_db_lock = Lock()
_accounts: Dict[str, Dict] = {}

class AccountCreate(BaseModel):
    owner: str = Field(..., example="Alice")
    initial_balance: float = Field(0.0, ge=0.0, example=100.0)

class AccountResponse(BaseModel):
    id: str
    owner: str
    balance: float

class AmountRequest(BaseModel):
    amount: float = Field(..., gt=0.0, example=25.5)

class TransferRequest(BaseModel):
    from_account_id: str
    to_account_id: str
    amount: float = Field(..., gt=0.0)

@app.get("/")
def root():
    return {"service": "BankAPI", "status": "running"}

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/accounts", response_model=AccountResponse, status_code=201)
def create_account(req: AccountCreate):
    acc_id = str(uuid4())
    with _db_lock:
        _accounts[acc_id] = {"id": acc_id, "owner": req.owner, "balance": float(req.initial_balance)}
    return _accounts[acc_id]

@app.get("/accounts/{account_id}", response_model=AccountResponse)
def get_account(account_id: str):
    acc = _accounts.get(account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    return acc

@app.post("/accounts/{account_id}/deposit", response_model=AccountResponse)
def deposit(account_id: str, req: AmountRequest):
    with _db_lock:
        acc = _accounts.get(account_id)
        if not acc:
            raise HTTPException(status_code=404, detail="Account not found")
        acc["balance"] += float(req.amount)
        return acc

@app.post("/accounts/{account_id}/withdraw", response_model=AccountResponse)
def withdraw(account_id: str, req: AmountRequest):
    with _db_lock:
        acc = _accounts.get(account_id)
        if not acc:
            raise HTTPException(status_code=404, detail="Account not found")
        if acc["balance"] < req.amount:
            raise HTTPException(status_code=400, detail="Insufficient funds")
        acc["balance"] -= float(req.amount)
        return acc

@app.post("/transfer")
def transfer(req: TransferRequest):
    if req.from_account_id == req.to_account_id:
        raise HTTPException(status_code=400, detail="Cannot transfer to same account")
    # simple ordering to avoid deadlocks
    a, b = sorted([req.from_account_id, req.to_account_id])
    with _db_lock:
        from_acc = _accounts.get(req.from_account_id)
        to_acc = _accounts.get(req.to_account_id)
        if not from_acc or not to_acc:
            raise HTTPException(status_code=404, detail="One or both accounts not found")
        if from_acc["balance"] < req.amount:
            raise HTTPException(status_code=400, detail="Insufficient funds")
        from_acc["balance"] -= float(req.amount)
        to_acc["balance"] += float(req.amount)
    return {"from": from_acc, "to": to_acc}

"# unfinished work"
def login(): pass

def logout() : pass

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
