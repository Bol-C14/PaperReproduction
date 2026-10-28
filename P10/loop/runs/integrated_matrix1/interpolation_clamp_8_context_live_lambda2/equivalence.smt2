; benchmark generated from python API
(set-info :status unknown)
(declare-fun a () (_ BitVec 8))
(declare-fun b () (_ BitVec 8))
(assert
 (let ((?x156 (bvmul ((_ zero_extend 2) ((_ extract 3 0) ((_ extract 3 0) a))) ((_ zero_extend 4) ((_ extract 1 0) (_ bv3 8))))))
(let ((?x19 (bvmul ((_ zero_extend 3) ((_ extract 3 0) ((_ extract 3 0) b))) ((_ zero_extend 4) ((_ extract 2 0) (_ bv5 8))))))
(let ((?x38 (bvadd ((_ extract 6 0) ((_ extract 6 0) ((_ zero_extend 1) ?x19))) ((_ zero_extend 1) ((_ extract 5 0) ((_ zero_extend 2) ?x156))))))
(let ((?x99 ((_ zero_extend 1) ?x38)))
(let ((?x10 (bvadd ((_ extract 7 0) (bvmul ((_ zero_extend 4) ((_ extract 3 0) a)) ((_ extract 7 0) (_ bv3 8)))) ((_ extract 7 0) (bvmul ((_ zero_extend 4) ((_ extract 3 0) b)) ((_ extract 7 0) (_ bv5 8)))))))
(and (distinct (ite (and (distinct (ite (bvult ?x10 (_ bv128 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) ?x10 (_ bv127 8)) (ite (and (distinct (ite (bvult ?x99 (_ bv128 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) ?x99 (_ bv127 8))) true)))))))
(check-sat)
