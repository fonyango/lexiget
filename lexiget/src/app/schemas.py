# src/app/schemas.py
from typing import List, Optional

from pydantic import BaseModel


class Address(BaseModel):
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zipcode: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class Party(BaseModel):
    name: Optional[str] = None
    address: Optional[Address] = None


class PaymentDetails(BaseModel):
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    payment_method: Optional[str] = None


class Item(BaseModel):
    name: Optional[str] = None
    unit_cost: Optional[float] = None
    quantity: Optional[float] = None
    amount: Optional[float] = None
    discount: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None


class InvoiceSchema(BaseModel):
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    currency: Optional[str] = None
    total_amount: Optional[float] = None
    seller: Optional[Party] = None
    buyer: Optional[Party] = None
    payment_details: Optional[PaymentDetails] = None
    items: List[Item] = []
    terms_and_conditions: Optional[str] = None


class ReceiptSchema(BaseModel):
    receipt_number: Optional[str] = None
    receipt_date: Optional[str] = None
    currency: Optional[str] = None
    total_amount: Optional[float] = None
    merchant: Optional[Party] = None
    payment_details: Optional[PaymentDetails] = None
    tax: Optional[float] = None
    items: List[Item] = []


class DeliveryItem(BaseModel):
    name: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    description: Optional[str] = None


class DeliveryNoteSchema(BaseModel):
    delivery_note_number: Optional[str] = None
    delivery_date: Optional[str] = None
    supplier: Optional[Party] = None
    customer: Optional[Party] = None
    delivery_address: Optional[Address] = None
    reference_number: Optional[str] = None
    transport_details: Optional[str] = None
    items: List[DeliveryItem] = []


class ContractParty(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None


class ContractSchema(BaseModel):
    contract_title: Optional[str] = None
    contract_number: Optional[str] = None
    effective_date: Optional[str] = None
    expiry_date: Optional[str] = None
    parties: List[ContractParty] = []
    obligations: Optional[str] = None
    payment_terms: Optional[str] = None
    termination_clause: Optional[str] = None
    governing_law: Optional[str] = None
