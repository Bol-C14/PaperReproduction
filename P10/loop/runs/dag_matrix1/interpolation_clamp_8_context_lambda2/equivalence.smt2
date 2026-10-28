; benchmark generated from python API
(set-info :status unknown)
(declare-fun a () (_ BitVec 8))
(declare-fun b () (_ BitVec 8))
(assert
 (let ((?x34 (bvmul ((_ zero_extend 2) ((_ extract 3 0) ((_ extract 3 0) a))) ((_ zero_extend 4) ((_ extract 1 0) (_ bv3 8))))))
(let ((?x161 (bvmul ((_ zero_extend 3) ((_ extract 3 0) ((_ extract 3 0) b))) ((_ zero_extend 4) ((_ extract 2 0) (_ bv5 8))))))
(let ((?x25 (bvadd ((_ extract 6 0) ((_ extract 6 0) ((_ zero_extend 1) ?x161))) ((_ zero_extend 1) ((_ extract 5 0) ((_ zero_extend 2) ?x34))))))
(let ((?x29 ((_ zero_extend 1) ?x25)))
(let ((?x273 (ite (and (distinct (ite (bvult ?x29 (_ bv128 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ?x29)))))) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) (_ bv127 8))))))))))
(let ((?x8 (bvadd ((_ extract 7 0) (bvmul ((_ zero_extend 4) ((_ extract 3 0) a)) ((_ extract 7 0) (_ bv3 8)))) ((_ extract 7 0) (bvmul ((_ zero_extend 4) ((_ extract 3 0) b)) ((_ extract 7 0) (_ bv5 8)))))))
(and (distinct (ite (and (distinct (ite (bvult ?x8 (_ bv128 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) ?x8 (_ bv127 8)) ?x273) true))))))))
(check-sat)
