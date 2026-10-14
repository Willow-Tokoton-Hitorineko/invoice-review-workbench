import copy
import csv
import io
import unittest
from workbench import evaluate,export_csv

class ReviewTests(unittest.TestCase):
    def row(self): return {'invoice_id':'DEMO-001','amount':'10.00','currency':'CNY','human_approval':{'category':'Office','project':'Demo','expense_date':'2026-01-01'}}
    def test_approved_can_export(self):
        self.assertIn('10.00',export_csv(evaluate([self.row()])))
    def test_date_not_filled_from_issue_date(self):
        r=self.row();r['human_approval'].pop('expense_date');r['issue_date']='2026-01-01'
        self.assertEqual(evaluate([r])[0]['status'],'REVIEW')
        with self.assertRaises(ValueError): export_csv(evaluate([r]))
    def test_duplicate_blocks_export(self):
        self.assertTrue(all(x['status']=='REVIEW' for x in evaluate([self.row(),self.row()])))
    def test_invalid_amounts(self):
        for amount in ('NaN','Infinity','-1','0','1.001'):
            r=self.row();r['amount']=amount
            self.assertEqual(evaluate([r])[0]['status'],'REJECT')
    def test_formula_injection(self):
        r=self.row();r['human_approval']['project']=' =HYPERLINK("https://example.invalid")'
        cells=list(csv.reader(io.StringIO(export_csv(evaluate([r])))))
        self.assertTrue(cells[1][4].startswith("'=HYPERLINK"))
    def test_invalid_actual_date(self):
        r=self.row();r['human_approval']['expense_date']='2026-02-30'
        self.assertEqual(evaluate([r])[0]['status'],'REJECT')
    def test_empty_batch_cannot_export(self):
        with self.assertRaises(ValueError):export_csv([])
    def test_source_is_unchanged(self):
        r=self.row();old=copy.deepcopy(r);evaluate([r]);self.assertEqual(r,old)
    def test_unknown_approval_key(self):
        r=self.row();r['human_approval']['auto']='yes'
        self.assertEqual(evaluate([r])[0]['status'],'REJECT')

if __name__=='__main__':unittest.main()
