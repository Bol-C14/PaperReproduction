; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(assert
 (let (($x12 (and (distinct (ite (bvsgt (_ bv4 8) a) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x16 (ite $x12 ((_ zero_extend 6) ((_ extract 1 0) (ite (bvslt a (_ bv0 8)) (bvneg a) a))) c)))
(and (distinct (ite $x12 (ite (bvslt a (_ bv0 8)) (bvneg a) a) c) ?x16) true))))
(check-sat)
