; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(assert
 (let ((?x34 (ite (and (distinct (ite (bvsgt (_ bv0 16) a) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) (bvneg ((_ extract 15 0) a)) a)))
(let (($x18 (and (distinct (ite (= (ite (bvsgt (_ bv65529 16) a) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x20 (ite (and (and (distinct (ite (bvsgt (_ bv8 16) a) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) $x18) (_ bv1 1) (_ bv0 1))))
(let ((?x29 (ite (and (distinct ?x20 (_ bv0 1)) true) ?x34 c)))
(and (distinct ?x29 ?x29) true))))))
(check-sat)
