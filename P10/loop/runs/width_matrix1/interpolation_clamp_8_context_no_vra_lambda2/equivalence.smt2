; benchmark generated from python API
(set-info :status unknown)
(declare-fun a () (_ BitVec 8))
(declare-fun b () (_ BitVec 8))
(assert
 (let ((?x18 ((_ extract 7 0) (bvmul ((_ zero_extend 4) ((_ extract 3 0) a)) ((_ extract 7 0) (_ bv3 8))))))
(let ((?x121 (bvadd ((_ extract 7 0) (bvmul ((_ extract 7 0) (_ bv5 8)) ((_ zero_extend 4) ((_ extract 3 0) b)))) ?x18)))
(let ((?x50 (ite (and (distinct (ite (bvult ?x121 (_ bv128 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) ((_ extract 7 0) ?x121) ((_ extract 7 0) (_ bv127 8)))))
(let ((?x179 (bvadd ?x18 ((_ extract 7 0) (bvmul ((_ zero_extend 4) ((_ extract 3 0) b)) ((_ extract 7 0) (_ bv5 8)))))))
(and (distinct (ite (and (distinct (ite (bvult ?x179 (_ bv128 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) ?x179 (_ bv127 8)) ?x50) true))))))
(check-sat)
