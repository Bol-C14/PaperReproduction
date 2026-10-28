; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(declare-fun b () (_ BitVec 8))
(assert
 (let ((?x15 (bvmul ((_ zero_extend 2) ((_ extract 2 0) ((_ extract 2 0) ((_ extract 2 0) b)))) ((_ zero_extend 3) ((_ extract 1 0) ((_ extract 7 0) a))))))
(let ((?x10 ((_ zero_extend 1) ((_ extract 4 0) ((_ zero_extend 3) ?x15)))))
(let (($x48 (and (distinct (ite (bvult a (_ bv4 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x5 ((_ extract 7 0) (bvmul ((_ extract 7 0) a) ((_ zero_extend 5) ((_ extract 2 0) b))))))
(and (distinct (ite $x48 (bvadd ?x5 ?x5) c) (ite $x48 ((_ zero_extend 2) (bvadd ?x10 ?x10)) ((_ extract 7 0) c))) true))))))
(check-sat)
