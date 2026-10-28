; benchmark generated from python API
(set-info :status unknown)
(declare-fun a () (_ BitVec 8))
(declare-fun c () (_ BitVec 8))
(assert
 (let ((?x13 (ite (bvslt a (_ bv0 8)) (bvneg a) a)))
(and (distinct (ite (and (distinct (ite (bvsgt (_ bv4 8) a) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) ?x13 c) ?x13) true)))
(check-sat)
