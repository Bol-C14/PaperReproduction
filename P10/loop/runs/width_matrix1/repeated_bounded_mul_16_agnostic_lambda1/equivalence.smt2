; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(assert
 (let ((?x1158 ((_ extract 15 0) (bvmul ((_ zero_extend 13) ((_ extract 2 0) b)) ((_ extract 15 0) a)))))
(let (($x114 (and (distinct (ite (bvult a (_ bv4 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x27 ((_ extract 15 0) (bvmul ((_ extract 15 0) a) ((_ zero_extend 13) ((_ extract 2 0) b))))))
(and (distinct (ite $x114 (bvadd ?x27 ?x27) c) (ite $x114 (bvadd ?x1158 ?x1158) c)) true)))))
(check-sat)
