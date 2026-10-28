; benchmark generated from python API
(set-info :status unknown)
(declare-fun b () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(assert
 (let ((?x21 (bvmul ((_ zero_extend 4) ((_ extract 2 0) (_ bv5 8))) ((_ zero_extend 3) ((_ extract 3 0) ((_ extract 3 0) b))))))
(let ((?x161 (bvmul ((_ zero_extend 4) ((_ extract 1 0) (_ bv3 8))) ((_ zero_extend 2) ((_ extract 3 0) ((_ extract 3 0) a))))))
(let ((?x25 (bvadd ((_ zero_extend 1) ((_ extract 5 0) ((_ zero_extend 2) ?x161))) ((_ extract 6 0) ((_ extract 6 0) ((_ zero_extend 1) ?x21))))))
(let ((?x29 ((_ zero_extend 1) ?x25)))
(let ((?x8 (bvadd ((_ extract 7 0) (bvmul ((_ zero_extend 4) ((_ extract 3 0) a)) ((_ extract 7 0) (_ bv3 8)))) ((_ extract 7 0) (bvmul ((_ zero_extend 4) ((_ extract 3 0) b)) ((_ extract 7 0) (_ bv5 8)))))))
(and (distinct (ite (and (distinct (ite (bvult ?x8 (_ bv128 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) ?x8 (_ bv127 8)) (ite (and (distinct (ite (bvult ?x29 (_ bv128 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) ?x29 (_ bv127 8))) true)))))))
(check-sat)
