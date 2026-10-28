; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(assert
 (let ((?x26 (ite (and (distinct (ite (bvult a (_ bv4 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) c (bvmul ((_ extract 15 0) a) ((_ zero_extend 13) ((_ extract 2 0) b))))))
(let ((?x55 (ite (and (distinct (ite (bvult a (_ bv16 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) ?x26 c)))
(and (distinct ?x55 ?x55) true))))
(check-sat)
