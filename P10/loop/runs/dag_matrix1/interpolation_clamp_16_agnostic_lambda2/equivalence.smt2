; benchmark generated from python API
(set-info :status unknown)
(declare-fun a () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(assert
 (let ((?x167 (bvmul ((_ zero_extend 2) ((_ extract 3 0) ((_ extract 3 0) a))) ((_ zero_extend 4) ((_ extract 1 0) (_ bv3 16))))))
(let ((?x18 (bvmul ((_ zero_extend 3) ((_ extract 3 0) ((_ extract 3 0) b))) ((_ zero_extend 4) ((_ extract 2 0) (_ bv5 16))))))
(let ((?x181 (bvadd ((_ extract 6 0) ((_ extract 6 0) ((_ zero_extend 9) ?x18))) ((_ zero_extend 1) ((_ extract 5 0) ((_ zero_extend 10) ?x167))))))
(let ((?x23 ((_ zero_extend 9) ?x181)))
(let ((?x12 (bvadd ((_ extract 15 0) (bvmul ((_ zero_extend 12) ((_ extract 3 0) a)) ((_ extract 15 0) (_ bv3 16)))) ((_ extract 15 0) (bvmul ((_ zero_extend 12) ((_ extract 3 0) b)) ((_ extract 15 0) (_ bv5 16)))))))
(and (distinct (ite (and (distinct (ite (bvult ?x12 (_ bv128 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) ?x12 (_ bv127 16)) (ite (and (distinct (ite (bvult ?x23 (_ bv128 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) ?x23 (_ bv127 16))) true)))))))
(check-sat)
