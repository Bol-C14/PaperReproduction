; benchmark generated from python API
(set-info :status unknown)
(declare-fun a () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(assert
 (let ((?x121 (bvadd ((_ extract 15 0) (bvmul ((_ extract 15 0) (_ bv5 16)) ((_ zero_extend 12) ((_ extract 3 0) b)))) ((_ extract 15 0) (bvmul ((_ extract 15 0) (_ bv3 16)) ((_ zero_extend 12) ((_ extract 3 0) a)))))))
(let ((?x17 (bvadd ((_ extract 15 0) (bvmul ((_ zero_extend 12) ((_ extract 3 0) a)) ((_ extract 15 0) (_ bv3 16)))) ((_ extract 15 0) (bvmul ((_ zero_extend 12) ((_ extract 3 0) b)) ((_ extract 15 0) (_ bv5 16)))))))
(and (distinct (ite (and (distinct (ite (bvult ?x17 (_ bv128 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) ?x17 (_ bv127 16)) (ite (and (distinct (ite (bvult ?x121 (_ bv128 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) ?x121 (_ bv127 16))) true))))
(check-sat)
