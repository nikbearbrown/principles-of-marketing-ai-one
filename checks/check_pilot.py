"""Exact arithmetic and invariant tests for an invented marketing pilot."""
from fractions import Fraction as F
from math import ceil
from pathlib import Path
import json
import unittest

DATA=Path(__file__).resolve().parents[1]/'data'/'pilot-windows.json'


def overlap_range(n,a,b):
    if not 0<=a<=n or not 0<=b<=n:
        raise ValueError('invalid interview margins')
    return max(0,a+b-n), min(a,b)


def result(c,n,fee=None):
    if not 0<=n<=c['capacity']:
        raise ValueError('fulfillment outside known capacity')
    margin=(c['fee'] if fee is None else fee)-c['wear']-c['handling']
    return n*margin-c['fixed_incremental'], (
        ceil(F(c['fixed_incremental'],margin)) if margin>0 else None)


def rate(n,d):
    if not 0<=n<=d:
        raise ValueError('invalid numerator')
    return F(n,d) if d else None


def metrics(row):
    c,v,r,f=map(row.__getitem__,('contacts','visits','requests','fulfilled'))
    q,g=map(row.__getitem__,('repeat_opportunities','repeat_loans'))
    if not 0<=f<=min(row['capacity'],r) or not 0<=q<=f:
        raise ValueError('invalid capacity or eligible repeat opportunities')
    return (rate(v,c),rate(r,v),rate(f,r),rate(f,c),rate(g,q))


class Checks(unittest.TestCase):
    def setUp(self):
        self.data=json.loads(DATA.read_text())
        self.c=self.data['cost_model']
        self.a,self.b=self.data['windows']

    def test_overlap_cannot_be_inferred(self):
        m=self.data['interview_margins']
        self.assertEqual(overlap_range(m['respondents'],m['transport_difficulty'],m['prior_borrowers']),(0,2))
        self.assertEqual(overlap_range(8,7,4),(3,4))

    def test_capacity_does_not_break_even(self):
        self.assertEqual(result(self.c,8),(-14,15))
        with self.assertRaises(ValueError):result(self.c,15)

    def test_higher_fee_not_a_demand_prediction(self):
        self.assertEqual(result(self.c,8,11),(2,8))
        self.assertEqual(result({**self.c,'capacity':6},6,11),(-6,8))
        self.assertEqual(result(self.c,6,10),(-12,10))
        self.assertEqual(result(self.c,8,7),(-30,None))

    def test_funnels_and_advantage(self):
        self.assertEqual(metrics(self.a),(F(2,5),F(3,8),F(2,3),F(1,10),F(2,3)))
        self.assertEqual(metrics(self.b),(F(3,10),F(5,12),F(1),F(1,8),F(1,2)))
        self.assertEqual(metrics(self.b)[3]-metrics(self.a)[3],F(1,40))

    def test_extra_pickup_without_extra_reach(self):
        a=metrics({**self.a,'fulfilled':5})
        self.assertEqual((a[0],a[2],a[3]),(F(2,5),F(5,6),F(1,8)))

    def test_bad_record_does_not_pass(self):
        with self.assertRaises(ValueError): metrics({**self.a,'fulfilled':7})
        with self.assertRaises(ValueError): metrics({**self.a,'repeat_opportunities':7})
        self.assertIsNone(rate(0,0))


if __name__=='__main__':
    unittest.main(verbosity=2)
