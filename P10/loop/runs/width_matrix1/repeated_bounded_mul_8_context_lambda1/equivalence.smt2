; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(declare-fun b () (_ BitVec 8))
(assert
 (let ((?x6 (bvmul ((_ zero_extend 2) ((_ extract 2 0) ((_ extract 2 0) ((_ extract 2 0) b)))) ((_ zero_extend 3) ((_ extract 1 0) ((_ extract 7 0) a))))))
(let ((?x179 ((_ zero_extend 1) ((_ extract 4 0) ((_ zero_extend 3) ?x6)))))
(let (($x114 (and (distinct (ite (bvult a (_ bv4 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x27 ((_ extract 7 0) (bvmul ((_ extract 7 0) a) ((_ zero_extend 5) ((_ extract 2 0) b))))))
(and (distinct (ite $x114 (bvadd ?x27 ?x27) c) (ite $x114 ((_ zero_extend 2) (bvadd ?x179 ?x179)) ((_ extract 7 0) c))) true))))))
(check-sat)
