; benchmark generated from python API
(set-info :status unknown)
(declare-fun b () (_ BitVec 1))
(declare-fun a () (_ BitVec 8))
(assert
 (let (($x15 (and (distinct (ite (= (ite (bvsgt (_ bv253 8) a) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x17 (ite (and (and (distinct (ite (bvsgt (_ bv4 8) a) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) $x15) (_ bv1 1) (_ bv0 1))))
(let (($x22 (and (distinct ?x17 (_ bv0 1)) true)))
(and (distinct (ite $x22 (ite (bvsgt (_ bv8 8) a) (_ bv1 1) (_ bv0 1)) b) (ite $x22 ((_ extract 0 0) (ite (bvsgt (_ bv8 8) a) (_ bv1 1) (_ bv0 1))) b)) true)))))
(check-sat)
