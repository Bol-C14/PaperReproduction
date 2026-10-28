; benchmark generated from python API
(set-info :status unknown)
(declare-fun b () (_ BitVec 1))
(declare-fun a () (_ BitVec 8))
(assert
 (let (($x14 (and (distinct (ite (bvsgt (_ bv1 8) a) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(and (distinct (ite $x14 (ite (bvsgt (_ bv0 8) a) (_ bv1 1) (_ bv0 1)) b) (ite $x14 (_ bv1 1) b)) true)))
(check-sat)
