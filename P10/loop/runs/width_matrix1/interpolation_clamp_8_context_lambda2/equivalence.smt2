; benchmark generated from python API
(set-info :status unknown)
(declare-fun b () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(assert
 (let ((?x68 (bvmul ((_ zero_extend 3) ((_ extract 3 0) ((_ extract 3 0) b))) ((_ zero_extend 4) ((_ extract 2 0) (_ bv5 8))))))
(let ((?x118 (bvmul ((_ zero_extend 2) ((_ extract 3 0) ((_ extract 3 0) a))) ((_ zero_extend 4) ((_ extract 1 0) (_ bv3 8))))))
(let ((?x589 (bvadd ((_ zero_extend 1) ((_ extract 5 0) ((_ zero_extend 2) ?x118))) ((_ extract 6 0) ((_ extract 6 0) ((_ zero_extend 1) ?x68))))))
(let ((?x2553 ((_ zero_extend 1) ?x589)))
(let ((?x922 (ite (and (distinct (ite (bvult ?x2553 (_ bv128 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ?x2553))))) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) (_ bv127 8)))))))))
(let ((?x179 (bvadd ((_ extract 7 0) (bvmul ((_ zero_extend 4) ((_ extract 3 0) a)) ((_ extract 7 0) (_ bv3 8)))) ((_ extract 7 0) (bvmul ((_ zero_extend 4) ((_ extract 3 0) b)) ((_ extract 7 0) (_ bv5 8)))))))
(and (distinct (ite (and (distinct (ite (bvult ?x179 (_ bv128 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) ?x179 (_ bv127 8)) ?x922) true))))))))
(check-sat)
