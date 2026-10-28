; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(assert
 (let ((?x12 ((_ extract 15 0) (bvmul ((_ extract 15 0) a) ((_ zero_extend 13) ((_ extract 2 0) b))))))
(let ((?x5 (ite (and (distinct (ite (bvult a (_ bv4 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true) (bvadd ?x12 ?x12) c)))
(and (distinct ?x5 ?x5) true))))
(check-sat)
