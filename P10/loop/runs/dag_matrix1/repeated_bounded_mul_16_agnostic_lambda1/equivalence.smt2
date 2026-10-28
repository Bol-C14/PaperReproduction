; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(assert
 (let ((?x277 ((_ extract 15 0) (bvmul ((_ zero_extend 13) ((_ extract 2 0) b)) ((_ extract 15 0) a)))))
(let (($x471 (and (distinct (ite (bvult a (_ bv4 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x25 ((_ extract 15 0) (bvmul ((_ extract 15 0) a) ((_ zero_extend 13) ((_ extract 2 0) b))))))
(and (distinct (ite $x471 (bvadd ?x25 ?x25) c) (ite $x471 (bvadd ?x277 ?x277) c)) true)))))
(check-sat)
