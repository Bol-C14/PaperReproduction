; benchmark generated from python API
(set-info :status unknown)
(declare-fun a () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(assert
 (let ((?x17 (bvmul ((_ zero_extend 2) ((_ extract 3 0) ((_ extract 3 0) a))) ((_ zero_extend 4) ((_ extract 1 0) (_ bv3 16))))))
(let ((?x22 (bvmul ((_ zero_extend 4) ((_ extract 2 0) (_ bv5 16))) ((_ zero_extend 3) ((_ extract 3 0) ((_ extract 3 0) b))))))
(let ((?x7 (bvadd ((_ extract 6 0) ((_ extract 6 0) ((_ zero_extend 9) ?x22))) ((_ zero_extend 1) ((_ extract 5 0) ((_ zero_extend 10) ?x17))))))
(let ((?x52 ((_ zero_extend 9) ?x7)))
(let ((?x134 (ite (and (distinct (ite (bvult ?x52 (_ bv128 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) ((_ extract 15 0) ((_ extract 15 0) ?x52)) (_ bv127 16))))
(let ((?x9 (bvadd ((_ extract 15 0) (bvmul ((_ zero_extend 12) ((_ extract 3 0) a)) ((_ extract 15 0) (_ bv3 16)))) ((_ extract 15 0) (bvmul ((_ zero_extend 12) ((_ extract 3 0) b)) ((_ extract 15 0) (_ bv5 16)))))))
(and (distinct (ite (and (distinct (ite (bvult ?x9 (_ bv128 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) ?x9 (_ bv127 16)) ?x134) true))))))))
(check-sat)
