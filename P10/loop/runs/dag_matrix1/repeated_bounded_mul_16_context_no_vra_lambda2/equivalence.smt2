; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 16))
(declare-fun a () (_ BitVec 16))
(declare-fun b () (_ BitVec 16))
(assert
 (let ((?x150 (bvmul ((_ zero_extend 13) ((_ extract 2 0) ((_ extract 2 0) ((_ extract 2 0) b)))) ((_ extract 15 0) ((_ extract 15 0) ((_ extract 15 0) a))))))
(let ((?x112 ((_ extract 15 0) ?x150)))
(let (($x24 (and (distinct (ite (bvult a (_ bv4 16)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x71 ((_ extract 15 0) (bvmul ((_ extract 15 0) a) ((_ zero_extend 13) ((_ extract 2 0) b))))))
(and (distinct (ite $x24 (bvadd ?x71 ?x71) c) (ite $x24 (bvadd ?x112 ?x112) ((_ extract 15 0) ((_ extract 15 0) c)))) true))))))
(check-sat)
