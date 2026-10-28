; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(assert
 (let ((?x26 (ite (and (distinct (ite (bvsgt (_ bv0 8) a) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) (bvneg ((_ extract 7 0) a)) a)))
(let (($x19 (and (distinct (ite (= (ite (bvsgt (_ bv249 8) a) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x21 (ite (and (and (distinct (ite (bvsgt (_ bv8 8) a) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) $x19) (_ bv1 1) (_ bv0 1))))
(let ((?x30 (ite (and (distinct ?x21 (_ bv0 1)) true) ?x26 c)))
(and (distinct ?x30 ?x30) true))))))
(check-sat)
