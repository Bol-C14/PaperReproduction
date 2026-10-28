; benchmark generated from python API
(set-info :status unknown)
(declare-fun b () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(assert
 (let ((?x15 ((_ extract 7 0) (bvmul ((_ zero_extend 4) ((_ extract 3 0) b)) ((_ extract 7 0) (_ bv5 8))))))
(let ((?x121 (bvadd ((_ extract 7 0) (bvmul ((_ extract 7 0) (_ bv3 8)) ((_ zero_extend 4) ((_ extract 3 0) a)))) ?x15)))
(let ((?x179 (bvadd ((_ extract 7 0) (bvmul ((_ zero_extend 4) ((_ extract 3 0) a)) ((_ extract 7 0) (_ bv3 8)))) ?x15)))
(and (distinct (ite (and (distinct (ite (bvult ?x179 (_ bv128 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) ?x179 (_ bv127 8)) (ite (and (distinct (ite (bvult ?x121 (_ bv128 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) ?x121 (_ bv127 8))) true)))))
(check-sat)
