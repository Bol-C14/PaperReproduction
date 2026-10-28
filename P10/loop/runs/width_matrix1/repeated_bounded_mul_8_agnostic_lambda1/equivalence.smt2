; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(declare-fun b () (_ BitVec 8))
(assert
 (let ((?x17 ((_ extract 7 0) (bvmul ((_ zero_extend 5) ((_ extract 2 0) b)) ((_ extract 7 0) a)))))
(let (($x70 (and (distinct (ite (bvult a (_ bv4 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x114 ((_ extract 7 0) (bvmul ((_ extract 7 0) a) ((_ zero_extend 5) ((_ extract 2 0) b))))))
(and (distinct (ite $x70 (bvadd ?x114 ?x114) c) (ite $x70 (bvadd ?x17 ?x17) c)) true)))))
(check-sat)
