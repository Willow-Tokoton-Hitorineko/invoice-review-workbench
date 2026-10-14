"""Independent, synthetic invoice review demo. No OCR, accounting policy or real invoices."""
from __future__ import annotations
import argparse
import csv
import io
import json
from collections import Counter
from decimal import Decimal, InvalidOperation
from datetime import date
from pathlib import Path

HUMAN_FIELDS = {'category', 'project', 'expense_date'}
def evaluate(rows: list[dict]) -> list[dict]:
    ids = [r.get('invoice_id', '') for r in rows]
    counts = Counter(ids)
    results = []
    for row in rows:
        errors, reasons = [], []
        invoice_id = row.get('invoice_id', '')
        if not isinstance(invoice_id, str) or not invoice_id.strip():
            errors.append('invoice_id is required')
        if counts[invoice_id] > 1:
            reasons.append('duplicate invoice_id in this batch')
        try:
            amount = Decimal(str(row.get('amount', '')))
            if not amount.is_finite() or amount <= 0 or amount.as_tuple().exponent < -2:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            errors.append('amount must be positive, finite and have at most two decimal places')
            amount = None
        currency = row.get('currency', '')
        if not isinstance(currency, str) or len(currency) != 3 or not currency.isalpha() or not currency.isupper():
            errors.append('explicit uppercase currency required')
        approval = row.get('human_approval', {})
        if not isinstance(approval, dict):
            errors.append('human_approval must be an object')
            approval = {}
        if any(k not in HUMAN_FIELDS for k in approval):
            errors.append('unknown human approval field')
        if not all(isinstance(approval.get(k), str) and approval[k].strip() for k in HUMAN_FIELDS):
            reasons.append('category, project and actual expense_date require human confirmation')
        if approval.get('expense_date'):
            try:
                value = approval['expense_date']
                if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
                    raise ValueError
            except (ValueError, TypeError):
                errors.append('expense_date must be a valid ISO YYYY-MM-DD date')
        # Invoice issue date is deliberately never used as an expense date fallback.
        status = 'REJECT' if errors else ('REVIEW' if reasons else 'APPROVED')
        fields = {k: str(approval.get(k, '')).strip() for k in sorted(HUMAN_FIELDS)}
        results.append({'invoice_id': invoice_id, 'amount': str(amount) if amount is not None else None,
                        'currency': currency, 'status': status, 'errors': errors, 'reasons': reasons,
                        'human_fields': fields})
    return results

def spreadsheet_safe(value):
    value = str(value)
    # Protect CSV opened by spreadsheet software from formula injection.
    return "'" + value if value.lstrip().startswith(('=', '+', '-', '@')) else value

def export_csv(results: list[dict]) -> str:
    if not results or any(r['status'] != 'APPROVED' for r in results):
        raise ValueError('Export blocked: every invoice must be approved and valid')
    buf = io.StringIO(newline='')
    writer = csv.writer(buf)
    writer.writerow(['invoice_id', 'amount', 'currency', 'category', 'project', 'expense_date'])
    for r in results:
        writer.writerow([spreadsheet_safe(x) for x in [r['invoice_id'], r['amount'], r['currency'],
                         r['human_fields']['category'], r['human_fields']['project'], r['human_fields']['expense_date']]])
    return buf.getvalue()

def load(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get('invoices'), list):
        raise ValueError('Expected an object containing invoices array')
    if len(payload['invoices']) > 200 or any(not isinstance(x, dict) for x in payload['invoices']):
        raise ValueError('Batch must contain at most 200 invoice objects')
    if any(not isinstance(x.get('invoice_id', ''), str) for x in payload['invoices']):
        raise ValueError('invoice_id must be a string')
    return payload['invoices']

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', nargs='?', type=Path, default=Path(__file__).parent/'samples/synthetic.json')
    parser.add_argument('--export', type=Path, help='Export approved batch; refuses to overwrite')
    args=parser.parse_args()
    result=evaluate(load(json.loads(args.input.read_text(encoding='utf-8'))))
    if args.export:
        text=export_csv(result)
        with args.export.open('x',encoding='utf-8-sig',newline='') as f: f.write(text)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
