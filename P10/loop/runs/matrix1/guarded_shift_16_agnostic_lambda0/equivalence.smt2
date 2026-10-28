; benchmark generated from python API
(set-info :status unknown)
(declare-fun b () (_ BitVec 16))
(declare-fun c () (_ BitVec 16))
(declare-fun y () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(assert
 (let ((?x15 (bvadd ((_ extract 15 0) (bvlshr ((_ extract 15 0) a) ((_ zero_extend 0) y))) ((_ extract 15 0) c))))
(let ((?x7 (ite (and (distinct (ite (bvult y (_ bv2 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) ?x15 b)))
(and (distinct ?x7 ?x7) true))))
(check-sat)
