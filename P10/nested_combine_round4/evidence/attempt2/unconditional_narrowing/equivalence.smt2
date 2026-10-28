; benchmark generated from python API
(set-info :status unknown)
(declare-fun b () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(declare-fun c () (_ BitVec 8))
(assert
 (let ((?x42 ((_ extract 7 0) (_ bv1 8))))
(let ((?x25 ((_ zero_extend 3) (bvmul ((_ zero_extend 2) ((_ extract 2 0) a)) ((_ zero_extend 3) ((_ extract 1 0) b))))))
(let ((?x68 (ite (and (distinct (ite (bvult b (_ bv4 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) (bvadd ((_ extract 7 0) (bvmul ((_ extract 7 0) a) ((_ extract 7 0) b))) ?x42) c)))
(and (distinct (ite (and (distinct (ite (bvult a (_ bv8 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) ?x68 c) (bvadd ((_ extract 7 0) ?x25) ?x42)) true)))))
(check-sat)
