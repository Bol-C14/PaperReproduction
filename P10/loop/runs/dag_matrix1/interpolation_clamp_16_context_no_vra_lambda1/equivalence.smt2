; benchmark generated from python API
(set-info :status unknown)
(declare-fun a () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(assert
 (let ((?x112 ((_ extract 15 0) (bvmul ((_ zero_extend 12) ((_ extract 3 0) b)) ((_ extract 15 0) (_ bv5 16))))))
(let ((?x36 (bvadd ?x112 ((_ extract 15 0) (bvmul ((_ extract 15 0) (_ bv3 16)) ((_ zero_extend 12) ((_ extract 3 0) a)))))))
(let ((?x29 (ite (and (distinct (ite (bvult ?x36 (_ bv128 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) ((_ extract 15 0) ?x36) ((_ extract 15 0) (_ bv127 16)))))
(let ((?x12 (bvadd ((_ extract 15 0) (bvmul ((_ zero_extend 12) ((_ extract 3 0) a)) ((_ extract 15 0) (_ bv3 16)))) ?x112)))
(and (distinct (ite (and (distinct (ite (bvult ?x12 (_ bv128 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) ?x12 (_ bv127 16)) ?x29) true))))))
(check-sat)
